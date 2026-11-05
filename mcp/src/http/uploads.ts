import { Readable, Transform } from 'node:stream';

import type { Express, Request as ExpressRequest, Response } from 'express';

import { formatMiB, isSafeFilename, isValidContentType, MAX_UPLOAD_BYTES } from '../core/files.js';
import { hashApiKey } from '../core/keys.js';
import type { UploadLinks, UploadStore } from '../core/ports.js';
import { nowSeconds } from '../core/time.js';
import { UPLOAD_TTL_SECONDS, type UploadRecord } from '../core/uploads.js';
import type { ClientFactory } from '../pneumatic/client.js';
import { pageHeaders, renderErrorPage, renderUploadDonePage, renderUploadPage } from './pages.js';
import type { Sealer } from './sealer.js';

// Longer than reading the body plus the storage upload timeout, so only a crashed process lets a lease lapse.
const UPLOAD_LEASE_SECONDS = 5 * 60;
const MAX_BODY_BYTES = MAX_UPLOAD_BYTES + 64 * 1024;
const MAX_CONCURRENT_UPLOADS = 4;

const PAGE_HEADERS = pageHeaders({ formActionSelf: true });

interface UploadToken {
  uploadId: string;
  apiKey: string;
}

class TooLargeError extends Error {}

// Binds the store to one API key for the tools; the sealed token in the link is the browser's capability.
export function uploadLinksFor(store: UploadStore, sealer: Sealer, publicUrl: URL, apiKey: string): UploadLinks {
  const keyHash = hashApiKey(apiKey);
  return {
    async create(filename) {
      const { uploadId, expiresAt } = await store.create(keyHash, filename ?? null, UPLOAD_TTL_SECONDS);
      const token = sealer.seal<UploadToken>('upload', { uploadId, apiKey }, UPLOAD_TTL_SECONDS);
      return { uploadId, uploadUrl: new URL(`/upload/${token}`, publicUrl).href, expiresAt };
    },
    async get(uploadId) {
      const entry = await store.get(uploadId);
      if (!entry || entry.keyHash !== keyHash) {
        return undefined;
      }
      const isExpired = !entry.file && entry.expiresAt < nowSeconds();
      return {
        uploadId,
        status: entry.file ? 'ready' : isExpired ? 'expired' : 'pending',
        filename: entry.filename,
        expiresAt: entry.expiresAt,
        file: entry.file,
      };
    },
  };
}

async function openLink(store: UploadStore, sealer: Sealer, token: string) {
  const payload = sealer.open<UploadToken>('upload', token);
  const entry = payload ? await store.get(payload.uploadId) : undefined;
  if (!payload || !entry || entry.file || entry.keyHash !== hashApiKey(payload.apiKey)) {
    return null;
  }
  return { apiKey: payload.apiKey, entry };
}

function sendInvalidLink(res: Response) {
  res.status(404).type('html').send(renderErrorPage('This upload link is invalid, expired or already used.'));
}

async function readFile(req: ExpressRequest): Promise<File | null> {
  if (Number(req.headers['content-length'] ?? 0) > MAX_BODY_BYTES) {
    throw new TooLargeError();
  }
  let total = 0;
  const limited = new Transform({
    transform(chunk: Buffer, _encoding, callback) {
      total += chunk.length;
      callback(total > MAX_BODY_BYTES ? new TooLargeError() : null, chunk);
    },
  });
  const body = Readable.toWeb(req.pipe(limited)) as ReadableStream<Uint8Array>;
  const form = await new Request('http://upload.local/', {
    method: 'POST',
    headers: { 'content-type': req.headers['content-type'] ?? '' },
    body,
    duplex: 'half',
  } as RequestInit).formData();
  const file = form.get('file');
  return file instanceof File ? file : null;
}

export function mountUploadRoutes(
  app: Express,
  { store, sealer, clientFor }: { store: UploadStore; sealer: Sealer; clientFor: ClientFactory },
) {
  const uploadLimit = formatMiB(MAX_UPLOAD_BYTES);
  // Each upload is buffered in memory, so concurrent uploads are bounded for the whole process.
  let activeUploads = 0;

  app.get('/upload/:token', async (req, res) => {
    res.set(PAGE_HEADERS);
    const upload = await openLink(store, sealer, req.params.token);
    if (!upload) {
      sendInvalidLink(res);
      return;
    }
    res.type('html').send(renderUploadPage({ filename: upload.entry.filename, limit: uploadLimit }));
  });

  app.post('/upload/:token', async (req, res) => {
    res.set(PAGE_HEADERS);
    const upload = await openLink(store, sealer, req.params.token);
    if (!upload) {
      sendInvalidLink(res);
      return;
    }
    // The slot is taken before any await so concurrent posts cannot all pass the check.
    if (activeUploads >= MAX_CONCURRENT_UPLOADS) {
      res.set('Retry-After', '10');
      res
        .status(503)
        .type('html')
        .send(
          renderUploadPage({
            filename: upload.entry.filename,
            limit: uploadLimit,
            error: 'The connector is busy. Try again in a few seconds.',
          }),
        );
      return;
    }
    activeUploads += 1;
    try {
      const leaseId = await store.claim(upload.entry.uploadId, UPLOAD_LEASE_SECONDS);
      if (!leaseId) {
        res.status(409).type('html').send(renderErrorPage('This file is already being uploaded or was uploaded.'));
        return;
      }
      try {
        await handleUpload(req, res, upload, leaseId);
      } finally {
        await store.release(upload.entry.uploadId, leaseId).catch(() => undefined);
      }
    } finally {
      activeUploads -= 1;
    }
  });

  async function handleUpload(
    req: ExpressRequest,
    res: Response,
    upload: { apiKey: string; entry: UploadRecord },
    leaseId: string,
  ) {
    const sendUploadError = (status: number, error: string) =>
      res
        .status(status)
        .type('html')
        .send(renderUploadPage({ filename: upload.entry.filename, limit: uploadLimit, error }));
    let file: File | null;
    try {
      file = await readFile(req);
    } catch (error) {
      return error instanceof TooLargeError
        ? sendUploadError(413, `The file exceeds ${uploadLimit}.`)
        : sendUploadError(400, 'The upload could not be read. Try again.');
    }
    if (!file || !file.size) {
      return sendUploadError(400, 'Choose a non-empty file.');
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      return sendUploadError(413, `The file exceeds ${uploadLimit}.`);
    }
    const name = [file.name, upload.entry.filename].find(isSafeFilename) ?? 'file';
    const contentType = isValidContentType(file.type) ? file.type : 'application/octet-stream';
    let stored;
    try {
      stored = await clientFor(upload.apiKey).upload({ data: file, filename: name, contentType });
    } catch {
      return sendUploadError(502, 'Pneumatic could not store the file. Try again later.');
    }
    // The file is in Pneumatic now; a lost lease or store error must not invite a duplicate upload.
    const isRecorded = await store
      .complete(upload.entry.uploadId, leaseId, { ...stored, name, contentType, size: file.size })
      .catch(() => false);
    if (!isRecorded) {
      res
        .status(500)
        .type('html')
        .send(
          renderErrorPage(
            'The file reached Pneumatic, but the connector could not record it. Ask Claude for a new link.',
          ),
        );
      return;
    }
    res.type('html').send(renderUploadDonePage(name));
  }
}

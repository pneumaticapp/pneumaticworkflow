import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import {
  fileLinkUrl,
  filenameFromDisposition,
  formatMiB,
  isSafeFilename,
  isValidContentType,
  MAX_INLINE_UPLOAD_BYTES,
  MAX_UPLOAD_BYTES,
  tryDecodeURIComponent,
} from '../core/files.js';
import type { UploadLinks } from '../core/ports.js';
import { UPLOAD_TTL_SECONDS } from '../core/uploads.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { fileIdSegment, isSafeFileId } from '../pneumatic/files.js';
import { assertPublicHttpsUrl } from '../pneumatic/remoteFile.js';
import { additive, readOnly } from './annotations.js';
import { present } from './output.js';
import { limit, offset, requireExactlyOne } from './schemas.js';

const MAX_INLINE_BYTES = 3 * 1024 * 1024;
const MAX_INLINE_TEXT_BYTES = 256 * 1024;
const INLINE_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/gif', 'image/webp']);
const TEXT_TYPE =
  /^(?:text\/|application\/(?:json|xml|csv|yaml|x-yaml|x-ndjson)$|application\/[\w.+-]+\+(?:json|xml)$)/;

const EXTENSION_TYPES: Record<string, string> = {
  txt: 'text/plain',
  md: 'text/markdown',
  csv: 'text/csv',
  json: 'application/json',
  xml: 'application/xml',
  pdf: 'application/pdf',
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  gif: 'image/gif',
  webp: 'image/webp',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xls: 'application/vnd.ms-excel',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ppt: 'application/vnd.ms-powerpoint',
  pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  zip: 'application/zip',
};

const filename = z.string().min(1).max(255).refine(isSafeFilename, {
  message: 'Expected a filename without path separators or control characters',
});

const contentType = z
  .string()
  .max(200)
  .refine(isValidContentType, { message: 'Expected a MIME type such as text/plain' });

function guessContentType(name: string): string {
  const extension = name.split('.').at(-1)?.toLowerCase() ?? '';
  return EXTENSION_TYPES[extension] ?? 'application/octet-stream';
}

function decodeBase64(value: string): Buffer {
  const payload = value.replace(/^data:[^,]*;base64,/, '').replace(/\s+/g, '');
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(payload) || payload.length % 4 === 1) {
    throw new ConnectorError('invalid_arguments', 'contentBase64 is not valid base64');
  }
  return Buffer.from(payload, 'base64');
}

function markdownLink(name: string, url: string): string {
  return `[${name.replace(/\[/g, '(').replace(/\]/g, ')')}](${url})`;
}

function requireFilesUrl(client: PneumaticClient): string {
  if (!client.filesUrl) {
    throw new ConnectorError('not_configured');
  }
  return client.filesUrl;
}

function fileIdFromUrl(value: string, filesUrl: string): string {
  const link = fileLinkUrl(value.trim()) ?? value.trim();
  let url: URL;
  try {
    url = new URL(link);
  } catch {
    throw new ConnectorError('invalid_arguments', 'Expected a Pneumatic file URL or a "[name](url)" file link');
  }
  const base = new URL(filesUrl);
  const prefix = `${base.pathname.replace(/\/+$/, '')}/`;
  const segment = url.pathname.startsWith(prefix) ? url.pathname.slice(prefix.length) : '';
  const fileId = tryDecodeURIComponent(segment) ?? '';
  if (url.host !== base.host || !segment || segment.includes('/') || !isSafeFileId(fileId)) {
    throw new ConnectorError('invalid_arguments', `Only Pneumatic file links under ${filesUrl}/ can be downloaded`);
  }
  return fileId;
}

function requireUploads(uploads: UploadLinks | undefined): UploadLinks {
  if (!uploads) {
    throw new ConnectorError('not_configured', 'Upload links are available only in http mode');
  }
  return uploads;
}

export const fileTools: ToolDef[] = [
  tool(
    'list_attachments',
    {
      title: 'List attachments',
      description:
        'List file attachments the connected user can access, with fileId, url, access and source type, with ' +
        'pagination. Files of a specific task or workflow are easier to find in fileLinks of get_task / ' +
        'get_workflow or in comment links of list_workflow_events. Use download_file to read a file.',
      inputSchema: z.strictObject({ limit, offset }),
      annotations: readOnly,
    },
    async ({ limit, offset }, { client }) => {
      const raw = await client.get('/attachments', { limit, offset });
      return present(client, (presenter) =>
        presenter.page(raw, { limit, offset }, (item) => presenter.attachment(item)),
      );
    },
  ),

  tool(
    'download_file',
    {
      title: 'Download file',
      description:
        'Read a Pneumatic file by fileId or by its URL / "[name](url)" link (from fileLinks, comments or ' +
        'list_attachments). Returns metadata in data and the file itself as extra content: images inline, text ' +
        `files up to ${MAX_INLINE_TEXT_BYTES / 1024} KiB as text, other files up to ${formatMiB(MAX_INLINE_BYTES)} ` +
        'as a base64 resource. Larger files return only metadata and the url to open in a browser signed in to Pneumatic.',
      inputSchema: z.strictObject({
        fileId: z.string().min(1).max(512).optional().describe('Storage file ID'),
        url: z.string().min(1).max(4096).optional().describe('Pneumatic file URL or Markdown file link'),
      }),
      annotations: readOnly,
    },
    async (args, { client }) => {
      const filesUrl = requireFilesUrl(client);
      requireExactlyOne(args, ['fileId', 'url']);
      const fileId = args.fileId ?? fileIdFromUrl(args.url ?? '', filesUrl);
      const segment = fileIdSegment(fileId);
      const url = `${filesUrl}/${segment}`;
      const file = await client.download(segment, MAX_INLINE_BYTES);
      const { data, contentType: mimeType } = file;
      const isText = TEXT_TYPE.test(mimeType);
      const isInline = data !== null && (!isText || data.length <= MAX_INLINE_TEXT_BYTES);
      const metadata = {
        fileId,
        name: filenameFromDisposition(file.disposition) ?? null,
        contentType: mimeType,
        size: file.size,
        url,
        inline: isInline,
      };
      if (!data || !isInline) {
        return {
          data: {
            ...metadata,
            note: 'The file is too large to return inline; open url in a browser signed in to Pneumatic.',
          },
        };
      }
      const base64 = data.toString('base64');
      if (INLINE_IMAGE_TYPES.has(mimeType)) {
        return { data: metadata, content: [{ type: 'image', data: base64, mimeType }] };
      }
      if (isText) {
        return {
          data: metadata,
          content: [{ type: 'resource', resource: { uri: url, mimeType, text: data.toString('utf8') } }],
        };
      }
      return { data: metadata, content: [{ type: 'resource', resource: { uri: url, mimeType, blob: base64 } }] };
    },
  ),

  tool(
    'upload_file',
    {
      title: 'Upload file',
      description:
        'Upload a file to Pneumatic storage from exactly one source: contentText (plain text you produced), ' +
        'contentBase64 (small binary data) or sourceUrl (a public HTTPS URL that the connector downloads). ' +
        `Limits: ${formatMiB(MAX_INLINE_UPLOAD_BYTES)} for inline content, ${formatMiB(MAX_UPLOAD_BYTES)} ` +
        'for sourceUrl. The file is not attached anywhere until you use the returned ' +
        'data.fieldValue: put it in a file field array of complete_task output, run_workflow or update_workflow ' +
        'kickoff, or into comment text. Repeating the call uploads another copy.',
      inputSchema: z.strictObject({
        filename: filename.optional().describe('File name with extension; required for contentText/contentBase64'),
        contentType: contentType.optional().describe('MIME type; guessed from the extension or the source if omitted'),
        contentText: z
          .string()
          .min(1)
          .max(MAX_INLINE_UPLOAD_BYTES)
          .optional()
          .describe('UTF-8 text content of the file'),
        contentBase64: z
          .string()
          .min(1)
          .max(Math.ceil(MAX_INLINE_UPLOAD_BYTES / 3) * 4 + 1024)
          .optional()
          .describe('Base64 file content (a data: URL prefix is allowed)'),
        sourceUrl: z
          .string()
          .max(2048)
          .optional()
          .describe('Public HTTPS URL (port 443, no credentials) to download the file from'),
      }),
      annotations: { ...additive, openWorldHint: true },
    },
    async (args, { client, fetchRemote }) => {
      requireFilesUrl(client);
      requireExactlyOne(args, ['contentText', 'contentBase64', 'sourceUrl']);
      let data: Buffer;
      let name = args.filename;
      let type = args.contentType;
      if (args.sourceUrl !== undefined) {
        let source: URL;
        try {
          source = new URL(args.sourceUrl);
        } catch {
          throw new ConnectorError('invalid_arguments', 'sourceUrl is not a valid URL');
        }
        assertPublicHttpsUrl(source);
        const remote = await fetchRemote(source, MAX_UPLOAD_BYTES);
        data = remote.data;
        name ??= remote.filename;
        type ??= isValidContentType(remote.contentType) ? remote.contentType : undefined;
      } else {
        if (!name) {
          throw new ConnectorError('invalid_arguments', 'filename is required for contentText and contentBase64');
        }
        data =
          args.contentText !== undefined
            ? Buffer.from(args.contentText, 'utf8')
            : decodeBase64(args.contentBase64 ?? '');
      }
      name = name && filename.safeParse(name).success ? name : 'file';
      type ??= guessContentType(name);
      if (!data.length) {
        throw new ConnectorError('invalid_arguments', 'The file is empty');
      }
      const maxBytes = args.sourceUrl === undefined ? MAX_INLINE_UPLOAD_BYTES : MAX_UPLOAD_BYTES;
      if (data.length > maxBytes) {
        throw new ConnectorError('too_large', `The file exceeds ${maxBytes} bytes`);
      }
      const { fileId, url } = await client.upload({ data, filename: name, contentType: type });
      return {
        data: { fileId, name, contentType: type, size: data.length, url, fieldValue: markdownLink(name, url) },
      };
    },
  ),

  tool(
    'create_upload_link',
    {
      title: 'Create file upload link',
      description:
        'Create a one-time browser page where the user picks a file on their device, for files you cannot pass ' +
        'as content (e.g. a document attached in the chat or a large binary). Give data.uploadUrl to the user, ' +
        'then call get_upload_status until data.status is ready and use data.file.fieldValue like the result of ' +
        `upload_file. The link expires at data.expiresAt (after ${UPLOAD_TTL_SECONDS / 60} minutes) and accepts one ` +
        `file up to ${formatMiB(MAX_UPLOAD_BYTES)}.`,
      inputSchema: z.strictObject({
        filename: filename.optional().describe('Expected file name, shown to the user on the upload page'),
      }),
      annotations: additive,
      requires: 'uploads',
    },
    async ({ filename: expected }, { uploads }) => ({ data: await requireUploads(uploads).create(expected) }),
  ),

  tool(
    'get_upload_status',
    {
      title: 'Get upload status',
      description:
        'Check a link from create_upload_link: status pending (the user has not uploaded yet; wait and ask the ' +
        'user), ready (data.file holds fileId, url and fieldValue) or expired (create a new link).',
      inputSchema: z.strictObject({ uploadId: z.uuid().describe('uploadId returned by create_upload_link') }),
      annotations: readOnly,
      requires: 'uploads',
      pairedWith: 'create_upload_link',
    },
    async ({ uploadId }, { uploads }) => {
      const status = await requireUploads(uploads).get(uploadId);
      if (!status) {
        throw new ConnectorError('not_found', 'Unknown upload link');
      }
      const { file } = status;
      return {
        data: { ...status, file: file && { ...file, fieldValue: markdownLink(file.name, file.url) } },
      };
    },
  ),
];

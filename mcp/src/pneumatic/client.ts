import { ConnectorError } from '../core/errors.js';
import { mediaType } from '../core/files.js';
import { hashApiKey } from '../core/keys.js';
import { count } from '../core/metrics.js';
import { VERSION } from '../core/version.js';

export const USER_AGENT = `pneumatic-mcp/${VERSION}`;

const REQUEST_TIMEOUT_MS = 30_000;

const FILE_TIMEOUT_MS = 120_000;

type QueryValue = string | number | boolean | Array<string | number> | null | undefined;

export type Query = Record<string, QueryValue>;

interface RequestOptions {
  query?: Query;
  body?: unknown;
}

export class PneumaticApiError extends Error {
  constructor(
    readonly status: number,
    readonly method: string,
    readonly path: string,
    readonly body: unknown,
  ) {
    super(`Pneumatic API ${status} on ${method} ${path}: ${describeErrorBody(body)}`);
    this.name = 'PneumaticApiError';
  }

  get detail(): string {
    return describeErrorBody(this.body);
  }
}

function describeErrorBody(body: unknown): string {
  if (typeof body === 'string') {
    return body.slice(0, 500) || 'empty response';
  }
  if (body && typeof body === 'object') {
    const { message, detail, details } = body as Record<string, unknown>;
    const text = typeof message === 'string' ? message : typeof detail === 'string' ? detail : undefined;
    if (text && details) {
      return `${text} ${JSON.stringify(details)}`;
    }
    return text ?? JSON.stringify(body).slice(0, 500);
  }
  return 'empty response';
}

function buildQuery(query: Query = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) {
      continue;
    }
    if (Array.isArray(value)) {
      if (value.length) {
        params.set(key, value.join(','));
      }
      continue;
    }
    params.set(key, String(value));
  }
  const serialized = params.toString();
  return serialized ? `?${serialized}` : '';
}

export interface FileUpload {
  data: Buffer | Blob;
  filename: string;
  contentType: string;
}

export interface StoredFile {
  fileId: string;
  url: string;
}

export interface DownloadedFile {
  contentType: string;
  disposition?: string;
  size: number | null;
  data: Buffer | null;
}

function countUpstream(target: string, method: string, status: number | 'failed') {
  count('pneumatic_requests_total', 'Requests to the Pneumatic API and file storage by status class', {
    target,
    method,
    status: typeof status === 'number' ? `${Math.floor(status / 100)}xx` : status,
  });
}

export interface PneumaticEndpoints {
  apiUrl: string;
  filesUrl?: string;
  filesInternalUrl?: string;
  appUrl?: string;
  fetchFn?: typeof fetch;
}

export function createPneumaticClient(
  { apiUrl, filesUrl, filesInternalUrl, appUrl, fetchFn = fetch }: PneumaticEndpoints,
  apiKey: string,
) {
  async function request<T>(method: string, path: string, { query, body }: RequestOptions = {}): Promise<T> {
    const headers: Record<string, string> = {
      Accept: 'application/json',
      Authorization: `Bearer ${apiKey}`,
      'User-Agent': USER_AGENT,
    };
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    let response: Response;
    try {
      response = await fetchFn(`${apiUrl}${path}${buildQuery(query)}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      });
    } catch (error) {
      countUpstream('api', method, 'failed');
      throw error;
    }
    countUpstream('api', method, response.status);

    const text = await response.text();
    const parsed = parseBody(text, response.headers.get('content-type'));
    if (!response.ok) {
      throw new PneumaticApiError(response.status, method, path, parsed);
    }
    return parsed as T;
  }

  async function fileRequest(method: string, path: string, body?: FormData): Promise<Response> {
    if (!filesUrl) {
      throw new ConnectorError('not_configured');
    }
    const send = async () => {
      let response: Response;
      try {
        response = await fetchFn(`${filesInternalUrl ?? filesUrl}${path}`, {
          method,
          headers: { Accept: '*/*', Authorization: `Bearer ${apiKey}`, 'User-Agent': USER_AGENT },
          body,
          redirect: 'manual',
          signal: AbortSignal.timeout(FILE_TIMEOUT_MS),
        });
      } catch (error) {
        countUpstream('storage', method, 'failed');
        throw error;
      }
      countUpstream('storage', method, response.status);
      return response;
    };
    let response = await send();
    if (response.status === 401) {
      // Storage resolves API keys through the backend token cache, which any backend call refills.
      await response.body?.cancel();
      await request('GET', '/accounts/user');
      response = await send();
    }
    if (!response.ok) {
      const text = await response.text();
      throw new PneumaticApiError(response.status, method, path, parseBody(text, response.headers.get('content-type')));
    }
    return response;
  }

  return {
    filesUrl,
    appUrl,
    // Stable per Pneumatic instance and key, used to cache account data without keeping the raw key.
    identity: hashApiKey(`${apiUrl}\n${apiKey}`),
    async upload({ data, filename, contentType }: FileUpload): Promise<StoredFile> {
      const form = new FormData();
      const blob = data instanceof Blob ? data : new Blob([data as Uint8Array<ArrayBuffer>], { type: contentType });
      form.append('file', blob, filename);
      const response = await fileRequest('POST', '/upload', form);
      const stored = parseBody(await response.text(), response.headers.get('content-type')) as Record<string, unknown>;
      if (typeof stored?.file_id !== 'string' || typeof stored.public_url !== 'string') {
        throw new ConnectorError('invalid_response', 'Pneumatic storage returned an unexpected upload response');
      }
      return { fileId: stored.file_id, url: stored.public_url };
    },
    async download(fileIdSegment: string, maxBytes: number): Promise<DownloadedFile> {
      const response = await fileRequest('GET', `/${fileIdSegment}`);
      const declared = Number(response.headers.get('content-length') ?? Number.NaN);
      const file: DownloadedFile = {
        contentType: mediaType(response.headers.get('content-type')) ?? 'application/octet-stream',
        disposition: response.headers.get('content-disposition') ?? undefined,
        size: Number.isFinite(declared) ? declared : null,
        data: null,
      };
      if (!response.body) {
        return { ...file, size: 0, data: Buffer.alloc(0) };
      }
      if (file.size !== null && file.size > maxBytes) {
        await response.body.cancel();
        return file;
      }
      const chunks: Uint8Array[] = [];
      let total = 0;
      // Leaving the loop early cancels the stream.
      for await (const chunk of response.body) {
        total += chunk.length;
        if (total > maxBytes) {
          return file;
        }
        chunks.push(chunk);
      }
      return { ...file, size: total, data: Buffer.concat(chunks) };
    },
    get<T = unknown>(path: string, query?: Query): Promise<T> {
      return request<T>('GET', path, { query });
    },
    post<T = unknown>(path: string, body?: unknown): Promise<T> {
      return request<T>('POST', path, { body: body ?? {} });
    },
    patch<T = unknown>(path: string, body: unknown): Promise<T> {
      return request<T>('PATCH', path, { body });
    },
    put<T = unknown>(path: string, body: unknown): Promise<T> {
      return request<T>('PUT', path, { body });
    },
    delete<T = unknown>(path: string): Promise<T> {
      return request<T>('DELETE', path);
    },
  };
}

export type PneumaticClient = ReturnType<typeof createPneumaticClient>;

export function createClientFactory(endpoints: PneumaticEndpoints) {
  return (apiKey: string) => createPneumaticClient(endpoints, apiKey);
}

export type ClientFactory = ReturnType<typeof createClientFactory>;

function parseBody(text: string, contentType: string | null): unknown {
  if (!text) {
    return null;
  }
  if (contentType?.includes('json')) {
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
  return text;
}

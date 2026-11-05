export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
export const MAX_INLINE_UPLOAD_BYTES = 5 * 1024 * 1024;

const FILE_LINK_PATTERN = String.raw`!?\[[^\]]+\]\((\S+?)(?:\s+"[^"]*")?\)`;
const FILE_LINK = new RegExp(`^${FILE_LINK_PATTERN}$`);

const SAFE_FILENAME = /^[^/\\\0\r\n]{1,255}$/;
const CONTENT_TYPE = /^[\w.+-]+\/[\w.+-]+$/;

export const isSafeFilename = (value: string | null | undefined): value is string =>
  typeof value === 'string' && SAFE_FILENAME.test(value) && value !== '.' && value !== '..';

export const isValidContentType = (value: string | null | undefined): value is string =>
  typeof value === 'string' && value.length <= 200 && CONTENT_TYPE.test(value);

export interface RemoteFile {
  data: Buffer;
  contentType?: string;
  filename?: string;
}

export const isFileLink = (value: string) => FILE_LINK.test(value);

export const fileLinkUrl = (value: string) => FILE_LINK.exec(value)?.[1];

export const fileLinksIn = (markdown: string) => markdown.match(new RegExp(FILE_LINK_PATTERN, 'g')) ?? [];

export const formatMiB = (bytes: number) => `${bytes / 1024 / 1024} MiB`;

export function mediaType(header: string | null | undefined): string | undefined {
  return header?.split(';')[0]?.trim() || undefined;
}

export function filenameFromDisposition(header: string | undefined): string | undefined {
  if (!header) {
    return undefined;
  }
  const encoded = /filename\*\s*=\s*utf-8''([^;]+)/i.exec(header)?.[1];
  if (encoded) {
    try {
      return decodeURIComponent(encoded.trim());
    } catch {
      // Fall back to the plain filename parameter.
    }
  }
  return /filename\s*=\s*"?([^";]+)"?/i.exec(header)?.[1]?.trim() || undefined;
}

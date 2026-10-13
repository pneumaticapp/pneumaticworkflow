export const MCP_BINARY_CONTENT_TYPE = 'application/octet-stream';

// Keep aligned with backend/src/mcp/file_metadata.py and storage's safe MIME set.
const SAFE_CONTENT_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/bmp',
  'image/tiff',
  'image/x-icon',
  'image/vnd.microsoft.icon',
  'application/pdf',
  'application/zip',
  'application/x-zip-compressed',
  'application/gzip',
  'application/x-tar',
  'application/x-7z-compressed',
  'application/x-rar-compressed',
  'application/msword',
  'application/vnd.ms-excel',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.oasis.opendocument.text',
  'application/vnd.oasis.opendocument.spreadsheet',
  'text/plain',
  'text/csv',
  'text/tab-separated-values',
  'audio/mpeg',
  'audio/wav',
  'audio/ogg',
  'audio/webm',
  'audio/aac',
  'audio/flac',
  'video/mp4',
  'video/webm',
  'video/ogg',
  'video/quicktime',
  'video/x-msvideo',
  'application/json',
  'application/xml',
  MCP_BINARY_CONTENT_TYPE,
]);

export function canonicalMcpContentType(value: string): string {
  const type = value.split(';')[0].trim().toLowerCase();
  return SAFE_CONTENT_TYPES.has(type) ? type : MCP_BINARY_CONTENT_TYPE;
}

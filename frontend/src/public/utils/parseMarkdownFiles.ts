import { TUploadedFile } from './uploadFiles';
import { getBrowserConfigEnv } from './getConfig';
import { getAttachmentTypeByFilename, getAttachmentTypeByUrl } from '../components/Attachments/utils/getAttachmentType';

/**
 * Parses a markdown string and extracts file-service links as TUploadedFile[].
 * Format: [filename](url)
 * Only includes links belonging to the file-service (matched via fileServiceUrl from config).
 *
 * @example
 * parseMarkdownToFiles("[doc.pdf](https://app.pneumatic.app/files/abc-123)")
 * // → [{ id: 'abc-123', name: 'doc.pdf', url: '...', size: 0 }]
 *
 * parseMarkdownToFiles("[Google](https://docs.google.com/...)")
 * // → [] (not a file-service link)
 */
export function parseMarkdownLinks(markdownValue: string | null | undefined): Array<{ name: string; url: string }> {
  if (!markdownValue) return [];

  // Matches both [name](url) and ![name](url) / ![name](url "title")
  const regex = /!?\[([^\]]+)\]\(([^)"]+)(?:\s+"[^"]*")?\)/g;
  const links: Array<{ name: string; url: string }> = [];
  let match = regex.exec(markdownValue);

  while (match !== null) {
    const [, name, rawUrl] = match;
    links.push({ name, url: rawUrl.trim() });
    match = regex.exec(markdownValue);
  }

  return links;
}

export function parseMarkdownToFiles(markdownValue: string | null | undefined): TUploadedFile[] {
  const { api: { fileServiceUrl } = { fileServiceUrl: '' } } = getBrowserConfigEnv() || {};
  const files: TUploadedFile[] = [];

  parseMarkdownLinks(markdownValue).forEach(({ name, url }) => {
    if (fileServiceUrl && (url === fileServiceUrl || url.startsWith(`${fileServiceUrl}/`))) {
      const fileId = url.split('?')[0].split('#')[0].split('/').filter(Boolean).pop() || url;
      const isImageByName = getAttachmentTypeByFilename(name) === 'image';
      const isImageByUrl = getAttachmentTypeByUrl(url) === 'image';
      const isImage = isImageByName || isImageByUrl;

      files.push({
        id: fileId,
        name,
        url,
        size: 0,
        thumbnailUrl: isImage ? url : undefined,
      });
    }
  });

  return files;
}

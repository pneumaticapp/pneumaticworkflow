import { TUploadedFile } from './uploadFiles';

/**
 * Парсит markdown строку и извлекает файловые ссылки в формате TUploadedFile[].
 * Формат markdown: [filename](url)
 *
 * @example
 * parseMarkdownToFiles("[doc.pdf](https://files.example.com/abc-123)")
 * // → [{ id: 'abc-123', name: 'doc.pdf', url: 'https://files.example.com/abc-123', size: 0 }]
 */
export function parseMarkdownToFiles(markdownValue: string | null | undefined): TUploadedFile[] {
  if (!markdownValue) return [];

  const regex = /\[([^\]]+)\]\(([^)]+)\)/g;
  const files: TUploadedFile[] = [];
  let match = regex.exec(markdownValue);

  while (match !== null) {
    const [, name, url] = match;
    const fileId = url.split('/').pop() || url;

    files.push({
      id: fileId,
      name,
      url,
      size: 0,
    });

    match = regex.exec(markdownValue);
  }

  return files;
}

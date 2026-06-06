import { TUploadedFile } from './uploadFiles';
import { getBrowserConfigEnv } from './getConfig';

/**
 * Парсит markdown строку и извлекает файловые ссылки в формате TUploadedFile[].
 * Формат markdown: [filename](url)
 * Фильтрует только ссылки, принадлежащие файл-сервису (по fileServiceUrl из конфигурации).
 *
 * @example
 * parseMarkdownToFiles("[doc.pdf](https://app.pneumatic.app/files/abc-123)")
 * // → [{ id: 'abc-123', name: 'doc.pdf', url: '...', size: 0 }]
 *
 * parseMarkdownToFiles("[Google](https://docs.google.com/...)")
 * // → [] (не файл-сервис)
 */
export function parseMarkdownToFiles(markdownValue: string | null | undefined): TUploadedFile[] {
  if (!markdownValue) return [];

  const { api: { fileServiceUrl } = { fileServiceUrl: '' } } = getBrowserConfigEnv() || {};
  const regex = /\[([^\]]+)\]\(([^)]+)\)/g;
  const files: TUploadedFile[] = [];
  let match = regex.exec(markdownValue);

  while (match !== null) {
    const [, name, url] = match;

    if (fileServiceUrl && (url === fileServiceUrl || url.startsWith(`${fileServiceUrl}/`))) {
      const fileId = url.split('/').pop() || url;

      files.push({
        id: fileId,
        name,
        url,
        size: 0,
      });
    }

    match = regex.exec(markdownValue);
  }

  return files;
}

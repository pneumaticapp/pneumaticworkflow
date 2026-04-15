import { downloadBlobInBrowser } from './downloadBlobInBrowser';

export const WORKFLOWS_CSV_MIME = 'text/csv;charset=utf-8';

export const WORKFLOWS_CSV_DEFAULT_FILENAME = 'workflows.csv';

const CSV_DELIMITER = ',';

const UTF8_BOM = '\uFEFF';

const CSV_QUOTE = '"';

const CSV_ESCAPED_QUOTE = '""';

export function escapeCsvCell(value: string): string {
  const needsQuoting = /[",\r\n]/.test(value);
  if (needsQuoting) {
    return CSV_QUOTE + value.replace(/"/g, CSV_ESCAPED_QUOTE) + CSV_QUOTE;
  }
  return value;
}

export function encodeWorkflowRowsToCsvString(rows: string[][]): string {
  const lines = rows.map((cells) =>
    cells.map((cell) => escapeCsvCell(cell ?? '')).join(CSV_DELIMITER),
  );
  return lines.join('\r\n');
}

export function buildWorkflowsCsvBlob(rows: string[][]): Blob {
  const body = encodeWorkflowRowsToCsvString(rows);
  return new Blob([UTF8_BOM + body], { type: WORKFLOWS_CSV_MIME });
}

export function downloadWorkflowsCsv(
  rows: string[][],
  filename = WORKFLOWS_CSV_DEFAULT_FILENAME,
): void {
  downloadBlobInBrowser(buildWorkflowsCsvBlob(rows), filename);
}

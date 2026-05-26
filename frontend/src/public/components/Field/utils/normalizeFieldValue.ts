export type TFieldValue = string | number | string[] | undefined;

export function normalizeFieldValue(value: TFieldValue): string {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.join('');
  return String(value);
}

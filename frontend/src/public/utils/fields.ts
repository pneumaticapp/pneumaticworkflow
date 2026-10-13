import { TExtraFieldValue } from '../types/template';

export function normalizeCheckboxValue(value?: TExtraFieldValue): string[] {
  if (Array.isArray(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    return value.split(', ');
  }
  return [];
}

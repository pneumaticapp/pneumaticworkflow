import type { IExtraFieldSelectionAPI } from '../../../types/template';

export function normalizeSelections(selections?: (IExtraFieldSelectionAPI | string)[]): string[] {
  if (!selections?.length) return [];
  return selections.map((item) => (typeof item === 'string' ? item : item.value));
}

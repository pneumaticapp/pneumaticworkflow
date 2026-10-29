import type { TSelectOption } from '../types';

export function filterCompactOption({ label, data }: { label: unknown; data: unknown }, input: string) {
  const option = data as TSelectOption;
  const searchText = option.searchByText ?? (typeof label === 'string' ? label : '');

  return !input || searchText.toLowerCase().includes(input.toLowerCase());
}

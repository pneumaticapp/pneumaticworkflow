import { TDropdownListOptions, TDropdownOptionBase, TDropdownOptionGroup } from './types';

export const isOptionGroup = <TOption extends TDropdownOptionBase>(
  item: TOption | TDropdownOptionGroup<TOption>,
): item is TDropdownOptionGroup<TOption> => Array.isArray((item as TDropdownOptionGroup<TOption>).options);

export const flattenOptions = <TOption extends TDropdownOptionBase>(
  options: TDropdownListOptions<TOption>,
): TOption[] => options.flatMap((item) => (isOptionGroup(item) ? item.options : [item]));

export const toArray = <TOption>(value: TOption | TOption[] | null | undefined): TOption[] => {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
};

/**
 * Stable identity for an option. Falls back to reference equality when an option
 * carries neither `value` nor `sourceId`.
 */
export const getDefaultOptionValue = <TOption extends TDropdownOptionBase>(option: TOption): string | undefined => {
  if (option.value !== undefined) return String(option.value);
  if (option.sourceId !== undefined && option.sourceId !== null) return String(option.sourceId);
  return undefined;
};

export const getOptionSearchText = <TOption extends TDropdownOptionBase>(
  option: TOption,
  getOptionLabel?: (option: TOption) => unknown,
): string => {
  const label = getOptionLabel ? getOptionLabel(option) : option.label;
  return typeof label === 'string' ? label : '';
};

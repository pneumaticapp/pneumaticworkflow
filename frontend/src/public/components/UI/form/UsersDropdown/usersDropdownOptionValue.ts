import { EOptionTypes, TUsersDropdownOption } from './UsersDropdown';

export const getUsersDropdownOptionValue = (optionType: EOptionTypes, id: number | string): string =>
  `${optionType}-${id}`;

export const isUsersDropdownOptionEqual = (
  a: Pick<TUsersDropdownOption, 'optionType' | 'id'>,
  b: Pick<TUsersDropdownOption, 'optionType' | 'id'>,
): boolean => a.optionType === b.optionType && a.id === b.id;

export const isUsersDropdownOptionSelected = (
  selectedOptions: ReadonlyArray<Pick<TUsersDropdownOption, 'optionType' | 'id' | 'value'>>,
  option: Pick<TUsersDropdownOption, 'optionType' | 'id' | 'value'>,
): boolean =>
  selectedOptions.some(
    (item) =>
      isUsersDropdownOptionEqual(item, option) ||
      (item.value !== undefined && option.value !== undefined && item.value === option.value),
  );

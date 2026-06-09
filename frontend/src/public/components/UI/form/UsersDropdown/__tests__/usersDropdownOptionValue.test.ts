/// <reference types="jest" />
import { EOptionTypes } from '../UsersDropdown';
import {
  getUsersDropdownOptionValue,
  isUsersDropdownOptionEqual,
  isUsersDropdownOptionSelected,
} from '../usersDropdownOptionValue';

describe('usersDropdownOptionValue', () => {
  it('generates prefixed value for user and group', () => {
    expect(getUsersDropdownOptionValue(EOptionTypes.User, 5)).toBe('user-5');
    expect(getUsersDropdownOptionValue(EOptionTypes.Group, 5)).toBe('group-5');
  });

  it('compares options by optionType and id', () => {
    expect(
      isUsersDropdownOptionEqual(
        { optionType: EOptionTypes.User, id: 5 },
        { optionType: EOptionTypes.Group, id: 5 },
      ),
    ).toBe(false);

    expect(
      isUsersDropdownOptionEqual(
        { optionType: EOptionTypes.User, id: 5 },
        { optionType: EOptionTypes.User, id: 5 },
      ),
    ).toBe(true);
  });

  it('does not cross-match user and group with the same id when checking selection', () => {
    const selected = [{ optionType: EOptionTypes.User, id: 5, value: 'user-5' }];
    const userOption = { optionType: EOptionTypes.User, id: 5, value: 'user-5' };
    const groupOption = { optionType: EOptionTypes.Group, id: 5, value: 'group-5' };

    expect(isUsersDropdownOptionSelected(selected, userOption)).toBe(true);
    expect(isUsersDropdownOptionSelected(selected, groupOption)).toBe(false);
  });

  it('falls back to value comparison for backward compatibility', () => {
    const selected = [{ optionType: EOptionTypes.User, id: 1, value: 'legacy-value' }];
    const option = { optionType: EOptionTypes.Group, id: 99, value: 'legacy-value' };

    expect(isUsersDropdownOptionSelected(selected, option)).toBe(true);
  });
});

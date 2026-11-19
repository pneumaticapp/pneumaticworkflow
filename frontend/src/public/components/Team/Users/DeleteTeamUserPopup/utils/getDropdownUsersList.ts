import type { TSelectOption } from '../../../../UI/Select/types';
import type { TUserListItem } from '../../../../../types/user';
import { getNotDeletedUsers, getUserFullName } from '../../../../../utils/users';

export type TUserDropdownOption = TUserListItem & TSelectOption;

export const getDropdownUsersList = (users: TUserListItem[]) => {
  const activeUsers = getNotDeletedUsers(users);

  const dropdownSelections: TUserDropdownOption[] = activeUsers.map((user) => ({
    ...user,
    value: String(user.id),
    label: getUserFullName(user)!,
  }));

  return dropdownSelections;
};

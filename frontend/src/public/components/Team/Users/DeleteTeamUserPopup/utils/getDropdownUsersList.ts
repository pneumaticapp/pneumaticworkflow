import type { TDropdownOptionBase } from '../../../../UI/DropdownList/types';
import type { TUserListItem } from '../../../../../types/user';
import { getNotDeletedUsers, getUserFullName } from '../../../../../utils/users';

export type TUserDropdownOption = TUserListItem & TDropdownOptionBase;

export const getDropdownUsersList = (users: TUserListItem[]) => {
  const activeUsers = getNotDeletedUsers(users);

  const dropdownSelections: TUserDropdownOption[] = activeUsers.map((user) => ({
    ...user,
    value: String(user.id),
    label: getUserFullName(user)!,
  }));

  return dropdownSelections;
};

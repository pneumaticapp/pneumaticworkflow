import { EUserStatus, TUserListItem } from '../../../types/user';
import { isArrayWithItems } from '../../../utils/helpers';

const DELETED_USER: TUserListItem = {
  id: -1,
  status: EUserStatus.Deleted,
  email: '',
  firstName: 'Deleted user',
  lastName: '',
  photo: '',
  phone: '',
  type: 'user',
};

export function getUserById(users: TUserListItem[], userId?: number | null): TUserListItem | null {

  if (!isArrayWithItems(users)) {
    return null;
  }

  if (!userId) {
    return DELETED_USER;
  }

  const user = users.find((localUser) => localUser.id === userId);

  if (!user) {
    return DELETED_USER;
  }

  return user;
}

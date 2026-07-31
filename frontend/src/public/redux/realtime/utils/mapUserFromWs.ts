import { EUserStatus, TUserListItem } from '../../../types/user';
import type { IWsUserData } from '../types';

export function mapWsUserToListItem(user: IWsUserData): TUserListItem {
  const { subordinatesIds: reportIds, ...userData } = user;

  return {
    ...userData,
    photo: user.photo ?? '',
    type: 'user',
    phone: '',
    status: EUserStatus.Active,
    reportIds,
    vacation: null,
  };
}

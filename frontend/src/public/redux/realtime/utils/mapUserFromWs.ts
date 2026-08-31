import { EUserStatus, TUserListItem } from '../../../types/user';
import type { IWsUserData } from '../types';

export function mapWsUserToListItem(user: IWsUserData): TUserListItem {
  const { subordinatesIds: reportIds, ...userData } = user;

  return {
    ...userData,
    photo: user.photo ?? '',
    type: 'user',
    phone: user.phone ?? '',
    status: user.status ?? EUserStatus.Active,
    reportIds,
    vacation: user.vacation ?? null,
  };
}

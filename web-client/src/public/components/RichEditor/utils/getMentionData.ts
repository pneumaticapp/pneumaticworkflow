/* eslint-disable */
/* prettier-ignore */
import { TMentionData } from '..';
import { EUserStatus, TUserListItem } from '../../../types/user';
import { getUserFullName } from '../../../utils/users';

export function getMentionData(users: TUserListItem[]): TMentionData[] {
  const mentions: TMentionData[] = users
    .filter(user => user.status && user.status === EUserStatus.Active)
    .map(user => {
      return {
        id: user.id,
        name: getUserFullName(user) || '',
      };
    });

  return mentions;
}

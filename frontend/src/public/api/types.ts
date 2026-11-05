import type { EUserStatus, TUserListItem } from '../types/user';

export type TResponseUser = TUserListItem[];

export interface IGetUsersConfig {
  type?: TUserListItem['type'];
  status?: (EUserStatus.Active | EUserStatus.Inactive | EUserStatus.Invited)[];
  isAi?: boolean;
}

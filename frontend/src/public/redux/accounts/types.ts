import { TUserListItem } from '../../types/user';

export type TActiveUsersCountFetchFinishedPayload = {
  activeUsers: number;
  tenantsActiveUsers: number;
};

export type TUsersFetchPayload = {
  showErrorNotification: boolean;
};

export interface ITeamFetchStartedProps {
  offset?: number;
}

export type TDeleteUserPayload = {
  userId: number;
  reassignedUserId: number | null;
};

export type TDeclineInvitePayload = {
  userId: number;
  inviteId: string;
  reassignedUserId: number | null;
};

export interface IChangeUserAdminProps {
  id: number;
  email: string;
  isAdmin: boolean;
}

export type TOpenDeleteUserModalPayload = {
  user: TUserListItem;
};

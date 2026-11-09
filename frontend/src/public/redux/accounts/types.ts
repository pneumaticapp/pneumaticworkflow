import type { IAccountPlan } from '../../types/account';
import type { EUserListSorting, TUserListItem } from '../../types/user';

export enum EDeleteUserModalState {
  Closed = 'closed',
  FetchingUserData = 'fetching-user-data',
  WaitingForAction = 'waiting-for-action',
  PerformingAction = 'performing-action',
}

export interface IAccounts {
  isLoading: boolean;
  planInfo: IAccountPlan;
  users: TUserListItem[];
  team: {
    list: TUserListItem[];
    isLoading: boolean;
  };
  userListSorting: EUserListSorting;
  deleteUserModal: {
    user: TUserListItem | null;
    userWorkflowsCount: number;
    state: EDeleteUserModalState;
  };
}

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

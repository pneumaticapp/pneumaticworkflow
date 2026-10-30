import type { EUserListSorting, TUserListItem } from '../../../types/user';

export interface IUsersProps {
  userListSorting: EUserListSorting;
}

export interface ITeamUserCardProps {
  user: TUserListItem;
  currentUserId: number;
  isSubscribed: boolean;
  onOpenVacationModal(user: TUserListItem): void;
}

type TUserRelationCallbacks = { onSuccess?: () => void; onError?: () => void };

export type TChangeUserManager = (userId: number, managerId: number | null, callbacks?: TUserRelationCallbacks) => void;

export type TChangeUserReports = (userId: number, reportIds: number[], callbacks?: TUserRelationCallbacks) => void;

export interface ITeamUserRelationsModalsProps {
  user: TUserListItem;
  isManagerModalOpen: boolean;
  isReportsModalOpen: boolean;
  onCloseManagerModal(): void;
  onCloseReportsModal(): void;
  handleChangeUserManager: TChangeUserManager;
  handleChangeUserReports: TChangeUserReports;
}

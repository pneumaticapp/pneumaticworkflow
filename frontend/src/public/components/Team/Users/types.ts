import type { IAIAgent } from '../../../api/ai/types';
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

export interface ITeamAgentProps {
  agent: IAIAgent;
  providerName?: string;
}

export interface IEditAIAgentModalProps {
  agent: IAIAgent;
  onClose(): void;
}

export interface ITeamUserProps {
  user: TUserListItem;
  isCurrentUser?: boolean;
  isSubscribed?: boolean;
  resendInvite(): void;
  handleToggleAdmin(user: TUserListItem): () => Promise<void>;
  handleChangeUserManager(
    userId: number,
    managerId: number | null,
    callbacks?: { onSuccess?: () => void; onError?: () => void },
  ): void;
  handleChangeUserReports(
    userId: number,
    reportIds: number[],
    callbacks?: { onSuccess?: () => void; onError?: () => void },
  ): void;
  openModal(): void;
  openVacationModal(): void;
}

export interface ITeamUserDetailsProps {
  user: TUserListItem;
}

export interface ITeamUserRelationsModalsProps {
  user: TUserListItem;
  isManagerModalOpen: boolean;
  isReportsModalOpen: boolean;
  onCloseManagerModal(): void;
  onCloseReportsModal(): void;
  handleChangeUserManager: ITeamUserProps['handleChangeUserManager'];
  handleChangeUserReports: ITeamUserProps['handleChangeUserReports'];
}

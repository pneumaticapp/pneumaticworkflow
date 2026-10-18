import type { IAIAgent } from '../../../api/ai/types';
import type { EUserListSorting, TUserListItem } from '../../../types/user';

export interface IUsersProps {
  userListSorting: EUserListSorting;
}

export type TTeamListItem = { kind: 'user'; user: TUserListItem } | { kind: 'agent'; agent: IAIAgent };

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

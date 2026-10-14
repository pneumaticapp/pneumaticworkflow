import type { IAIAgent } from '../../../types/ai';
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

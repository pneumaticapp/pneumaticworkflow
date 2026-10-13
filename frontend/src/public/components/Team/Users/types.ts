import type { IAIAgent } from '../../../types/ai';
import type { EUserListSorting, TUserListItem } from '../../../types/user';

export interface IUsersProps {
  userListSorting: EUserListSorting;
}

export type TTeamListItem = { kind: 'user'; user: TUserListItem } | { kind: 'agent'; agent: IAIAgent };

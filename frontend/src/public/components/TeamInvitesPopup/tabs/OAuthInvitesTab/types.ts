import type { EInvitesType, IUserInvite } from '../../../../types/team';
import type { TUserListItem } from '../../../../types/user';

export interface IOAuthInvitesTabProps {
  users: IUserInvite[];
  teamUsers: TUserListItem[];
  type: EInvitesType;
}

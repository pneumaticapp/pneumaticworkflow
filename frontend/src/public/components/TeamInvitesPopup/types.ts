import type { TUserListItem } from '../../types/user';
import type { IUserInvite } from '../../types/team';

export interface ITeamInvitesPopupProps {
  children?: any;
  isTeamInvitesOpened: boolean;
  invitesUsersList: IUserInvite[];
  teamUsers: TUserListItem[];
  closeTeamInvitesPopup(): void;
}

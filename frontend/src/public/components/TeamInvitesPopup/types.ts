import { UserInvite } from "../../types/team";
import { TUserListItem } from "../../types/user";

export interface ITeamInvitesPopupProps {
  children?: any,
  isTeamInvitesOpened: boolean;
  invitesUsersList: UserInvite[];
  teamUsers: TUserListItem[];
  closeTeamInvitesPopup(): void;
}
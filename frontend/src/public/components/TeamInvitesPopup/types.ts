import { TUserListItem } from "../../types/user";
import { UserInvite } from "../../redux/team/types";

export interface ITeamInvitesPopupProps {
  children?: any,
  isTeamInvitesOpened: boolean;
  invitesUsersList: UserInvite[];
  teamUsers: TUserListItem[];
  closeTeamInvitesPopup(): void;
}
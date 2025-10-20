import { UserInvite, InvitesType } from "../../../../types/team";
import { TUserListItem } from "../../../../types/user";

export interface IOAuthInvitesTabProps {
  users: UserInvite[];
  teamUsers: TUserListItem[];
  type: InvitesType;
}
import { UserInvite, InvitesType } from "../../../../redux/team/types";
import { TUserListItem } from "../../../../types/user";

export interface IOAuthInvitesTabProps {
  users: UserInvite[];
  teamUsers: TUserListItem[];
  type: InvitesType;
}
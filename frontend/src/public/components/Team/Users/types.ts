import { IChangeUserAdminProps, ITeamFetchStartedProps, TOpenDeleteUserModalPayload } from "../../../redux/actions";
import { EUserListSorting, TUserListItem } from "../../../types/user";

export interface IUsersProps {
  currentUserId: number;
  isLoading?: boolean;
  sorting?: EUserListSorting;
  users: TUserListItem[];
  isTeamInvitesOpened?: boolean;
  isSubscribed?: boolean;
  trialEnded: boolean | null;
  userListSorting: EUserListSorting;
  fetchUsers(payload: ITeamFetchStartedProps): void;
  loadChangeUserAdmin(payload: IChangeUserAdminProps): void;
  openModal(params: TOpenDeleteUserModalPayload): void;
  openTeamInvitesPopup(): void;
  loadInvitesUsers(): void;
  setGeneralLoaderVisibility(isVisible: boolean): void;
}
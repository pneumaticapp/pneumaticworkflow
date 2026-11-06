import type { IUserInvite, IUserInvitePayload } from '../../types/team';
import type { TUserListItem } from '../../types/user';

export enum ETeamPages {
  Users = 'users',
  Groups = 'groups',
}

export type TInviteUsersPayload = {
  invites: IUserInvitePayload[];
  withGeneralLoader?: boolean;
  withSuccessNotification?: boolean;
  onStartUploading?(): void;
  onEndUploading?(): void;
  onError?(): void;
};

export interface ITeamStore {
  page: ETeamPages;
  isInvitesPopupOpen: boolean;
  recentInvitedUsers: TUserListItem[];
  invitesUsersList: IUserInvite[];
}

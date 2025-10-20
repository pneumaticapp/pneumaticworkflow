import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import { ETeamPages, UserInvite, UserInvitePayload } from '../../types/team';



export const enum ETeamActions {
  OpenPopup = 'OPEN_TEAM_INVITES_POPUP',
  ClosePopup = 'CLOSE_TEAM_INVITES_POPUP',
  InviteUsers = 'INVITE_USERS',
  SetRecentInvitedUsers = 'SET_RECENT_INVITED_USERS',

  LoadInvitesUsers = 'LOAD_INVITES_USERS',
  LoadInvitesUsersSuccess = 'LOAD_INVITES_USERS_SUCCESS',
  LoadInvitesUsersFailed = 'LOAD_INVITES_USERS_FAILED',

  UpdateTeamActiveTab = '_TEAM_ACTIVE_TAB',
  ChangeTeamActiveTab = 'CHANGE_TEAM_ACTIVE_TAB',
  SetTeamActivePage = 'SET_TEAM_PAGE',
}

export type TSetTeamActivePage = ITypedReduxAction<ETeamActions.SetTeamActivePage, ETeamPages>;
export const setTeamActivePage: (payload: ETeamPages) => TSetTeamActivePage = actionGenerator<
  ETeamActions.SetTeamActivePage,
  ETeamPages
>(ETeamActions.SetTeamActivePage);

export type TChangeTeamActiveTab = ITypedReduxAction<ETeamActions.ChangeTeamActiveTab, ETeamPages>;
export const changeTeamActiveTab: (payload: ETeamPages) => TChangeTeamActiveTab = actionGenerator<
  ETeamActions.ChangeTeamActiveTab,
  ETeamPages
>(ETeamActions.ChangeTeamActiveTab);

export type TUpdateTeamActiveTab = ITypedReduxAction<ETeamActions.UpdateTeamActiveTab, ETeamPages>;
export const updateTeamActiveTab: (payload: ETeamPages) => TUpdateTeamActiveTab = actionGenerator<
  ETeamActions.UpdateTeamActiveTab,
  ETeamPages
>(ETeamActions.UpdateTeamActiveTab);

type TOpenAction = ITypedReduxAction<ETeamActions.OpenPopup, void>;
export const openTeamInvitesPopup: (payload?: void) => TOpenAction = actionGenerator<ETeamActions.OpenPopup, void>(
  ETeamActions.OpenPopup,
);

type TCloseAction = ITypedReduxAction<ETeamActions.ClosePopup, void>;
export const closeTeamInvitesPopup: (payload?: void) => TCloseAction = actionGenerator<ETeamActions.ClosePopup, void>(
  ETeamActions.ClosePopup,
);

export type TInviteUsersPayload = {
  invites: UserInvitePayload[];
  withGeneralLoader?: boolean;
  withSuccessNotification?: boolean;
  onStartUploading?(): void;
  onEndUploading?(): void;
  onError?(): void;
};
export type TInviteUsers = ITypedReduxAction<ETeamActions.InviteUsers, TInviteUsersPayload>;
export const inviteUsers: (payload: TInviteUsersPayload) => TInviteUsers = actionGenerator<
  ETeamActions.InviteUsers,
  TInviteUsersPayload
>(ETeamActions.InviteUsers);

export type TSetRecentInvitedUsers = ITypedReduxAction<ETeamActions.SetRecentInvitedUsers, TUserListItem[]>;
export const setRecentInvitedUsers: (payload: TUserListItem[]) => TSetRecentInvitedUsers = actionGenerator<
  ETeamActions.SetRecentInvitedUsers,
  TUserListItem[]
>(ETeamActions.SetRecentInvitedUsers);

export type TLoadInvitesUsers = ITypedReduxAction<ETeamActions.LoadInvitesUsers, void>;
export const loadInvitesUsers: (payload?: void) => TLoadInvitesUsers = actionGenerator<
  ETeamActions.LoadInvitesUsers,
  void
>(ETeamActions.LoadInvitesUsers);

export type TLoadInvitesUsersSuccess = ITypedReduxAction<
  ETeamActions.LoadInvitesUsersSuccess,
  UserInvite[]
>;
export const loadInvitesUsersSuccess: (payload: UserInvite[]) => TLoadInvitesUsersSuccess =
  actionGenerator<ETeamActions.LoadInvitesUsersSuccess, UserInvite[]>(
    ETeamActions.LoadInvitesUsersSuccess,
  );

export type TLoadInvitesUsersFailed = ITypedReduxAction<ETeamActions.LoadInvitesUsersFailed, void>;
export const loadInvitesUsersFailed: (payload?: void) => TLoadInvitesUsersFailed = actionGenerator<
  ETeamActions.LoadInvitesUsersFailed,
  void
>(ETeamActions.LoadInvitesUsersFailed);



export type TTeamModalActions =
  | TOpenAction
  | TCloseAction
  | TInviteUsers
  | TSetRecentInvitedUsers
  | TLoadInvitesUsers
  | TLoadInvitesUsersSuccess
  | TLoadInvitesUsersFailed
  | TChangeTeamActiveTab
  | TUpdateTeamActiveTab
  | TSetTeamActivePage;

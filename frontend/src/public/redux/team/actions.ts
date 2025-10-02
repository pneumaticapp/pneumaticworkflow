import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import { ETeamPages, IOAuthInviteView, IUserInvite, IUserInviteMicrosoft } from '../../types/team';

export const enum ETeamActions {
  OpenPopup = 'OPEN_TEAM_INVITES_POPUP',
  ClosePopup = 'CLOSE_TEAM_INVITES_POPUP',
  InviteUsers = 'INVITE_USERS',
  SetRecentInvitedUsers = 'SET_RECENT_INVITED_USERS',
  ChangeGoogleInvites = 'CHANGE_GOOGLE_INVITES',

  LoadMicrosoftInvites = 'LOAD_MICROSOFT_INVITES',
  LoadMicrosoftInvitesSuccess = 'LOAD_MICROSOFT_INVITES_SUCCESS',
  LoadMicrosoftInvitesFailed = 'LOAD_MICROSOFT_INVITES_FAILED',

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
  invites: IUserInvite[];
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

export type TChangGoogleInvites = ITypedReduxAction<ETeamActions.ChangeGoogleInvites, IOAuthInviteView[]>;
export const changeGoogleInvites: (payload: IOAuthInviteView[]) => TChangGoogleInvites = actionGenerator<
  ETeamActions.ChangeGoogleInvites,
  IOAuthInviteView[]
>(ETeamActions.ChangeGoogleInvites);

export type TLoadMicrosoftInvites = ITypedReduxAction<ETeamActions.LoadMicrosoftInvites, void>;
export const loadMicrosoftInvites: (payload?: void) => TLoadMicrosoftInvites = actionGenerator<
  ETeamActions.LoadMicrosoftInvites,
  void
>(ETeamActions.LoadMicrosoftInvites);

export type TLoadMicrosoftInvitesSuccess = ITypedReduxAction<
  ETeamActions.LoadMicrosoftInvitesSuccess,
  IUserInviteMicrosoft[]
>;
export const loadMicrosoftInvitesSuccess: (payload: IUserInviteMicrosoft[]) => TLoadMicrosoftInvitesSuccess =
  actionGenerator<ETeamActions.LoadMicrosoftInvitesSuccess, IUserInviteMicrosoft[]>(
    ETeamActions.LoadMicrosoftInvitesSuccess,
  );

export type TLoadMicrosoftInvitesFailed = ITypedReduxAction<ETeamActions.LoadMicrosoftInvitesFailed, void>;
export const loadMicrosoftInvitesFailed: (payload?: void) => TLoadMicrosoftInvitesFailed = actionGenerator<
  ETeamActions.LoadMicrosoftInvitesFailed,
  void
>(ETeamActions.LoadMicrosoftInvitesFailed);

export type TTeamModalActions =
  | TOpenAction
  | TCloseAction
  | TInviteUsers
  | TSetRecentInvitedUsers
  | TChangGoogleInvites
  | TLoadMicrosoftInvites
  | TLoadMicrosoftInvitesSuccess
  | TLoadMicrosoftInvitesFailed
  | TChangeTeamActiveTab
  | TUpdateTeamActiveTab
  | TSetTeamActivePage;

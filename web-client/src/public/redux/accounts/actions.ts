/* eslint-disable */
/* prettier-ignore */
import { EUserListSorting, TUserListItem } from '../../types/user';
import { actionGenerator } from '../../utils/redux';
import { EDeleteUserModalState, IAccountPlan, ITypedReduxAction } from '../../types/redux';

export const enum EAccountsActions {
  UsersFetchStarted = 'USERS_FETCH_STARTED',
  UsersFetchFinished = 'USERS_FETCH_FINISHED',
  UsersFetchFailed = 'USERS_FETCH_FAILED',
  ActiveUsersCountFetchStarted = 'ACTIVE_USERS_COUNT_FETCH_STARTED',
  ActiveUsersCountFetchFinished = 'ACTIVE_USERS_COUNT_FETCH_FINISHED',
  TeamFetchStarted = 'TEAM_FETCH_STARTED',
  TeamFetchFinished = 'TEAM_FETCH_FINISHED',
  TeamFetchFailed = 'TEAM_FETCH_FAILED',
  UserListSortingChanged = 'USER_LIST_SORTING_CHANGED',
  SetCurrentPlan = 'SET_CURRENT_PLAN',
  FetchCurrentPlanFailed = 'FETCH_CURRENT_PLAN_FAILED',
  ChangeUserAdmin = 'CHANGE_USER_ADMIN',
  LoadChangeUserAdmin = 'LOAD_CHANGE_USER_ADMIN',
  DeleteUser = 'DELETE_USER',
  DeclineInvite = 'DECLINE_INVITE',
  SetDeleteUserModalState = 'SET_DELETE_USER_MODAL_STATE',
  OpenDeleteUserModal = 'OPEN_DELETE_USER_MODAL',
  CloseDeleteUserModal = 'CLOSE_DELETE_USER_MODAL',
  SetWorkflowsCount = 'SET_USER_WORKFLOWS_COUNT',
  ResetUsers = 'RESET_USERS',
  SetIsLoading = 'SET_IS_LOADING',
  FetchPlan = 'FETCH_PLAN',
  StartTrialSubscription = 'START_TRIAL_SUBSCRIPTION',
  StartFreeSubscription = 'START_FREE_SUBSCRIPTION',
  ShowPlanExpiredMessage = 'SHOW_PLAN_EXPIRED_MESSAGE',
}

export type TSetIsLoading = ITypedReduxAction<EAccountsActions.SetIsLoading, void>;
export const setIsLoadingAction: (payload?: void) => TSetIsLoading =
  actionGenerator<EAccountsActions.SetIsLoading, void>(EAccountsActions.SetIsLoading);

export type TResetUsers = ITypedReduxAction<EAccountsActions.ResetUsers, void>;
export const resetUsers: (payload?: void) => TResetUsers =
  actionGenerator<EAccountsActions.ResetUsers, void>(EAccountsActions.ResetUsers);

type TUsersFetchPayload = {
  showErrorNotification: boolean;
};

export type TUsersFetchStarted = ITypedReduxAction<EAccountsActions.UsersFetchStarted, TUsersFetchPayload>;
export const usersFetchStarted: (payload?: TUsersFetchPayload) => TUsersFetchStarted =
  actionGenerator<EAccountsActions.UsersFetchStarted, TUsersFetchPayload>(EAccountsActions.UsersFetchStarted);

export type TFetchCurrentPlanFailed = ITypedReduxAction<EAccountsActions.FetchCurrentPlanFailed, void>;
export const fetchCurrentPlanFailed: (payload?: void) => TFetchCurrentPlanFailed =
  actionGenerator<EAccountsActions.FetchCurrentPlanFailed, void>(EAccountsActions.FetchCurrentPlanFailed);

export type TUsersFetchFailed = ITypedReduxAction<EAccountsActions.UsersFetchFailed, void>;
export const usersFetchFailed: (payload?: void) => TUsersFetchFailed =
  actionGenerator<EAccountsActions.UsersFetchFailed, void>(EAccountsActions.UsersFetchFailed);

export type TUsersFetchFinished = ITypedReduxAction<EAccountsActions.UsersFetchFinished, TUserListItem[]>;
export const usersFetchFinished: (payload: TUserListItem[]) => TUsersFetchFinished =
  actionGenerator<EAccountsActions.UsersFetchFinished, TUserListItem[]>(EAccountsActions.UsersFetchFinished);

export type TActiveUsersCountFetchStarted = ITypedReduxAction<EAccountsActions.ActiveUsersCountFetchStarted, void>;
export const loadActiveUsersCount: (payload?: void) => TActiveUsersCountFetchStarted =
  actionGenerator<EAccountsActions.ActiveUsersCountFetchStarted, void>(EAccountsActions.ActiveUsersCountFetchStarted);

type TActiveUsersCountFetchFinishedPayload = {
  activeUsers: number;
  tenantsActiveUsers: number;
}
export type TActiveUsersCountFetchFinished = ITypedReduxAction<EAccountsActions.ActiveUsersCountFetchFinished, TActiveUsersCountFetchFinishedPayload>;
export const activeUsersCountFetchFinished: (payload: TActiveUsersCountFetchFinishedPayload) => TActiveUsersCountFetchFinished =
  actionGenerator<EAccountsActions.ActiveUsersCountFetchFinished, TActiveUsersCountFetchFinishedPayload>(
    EAccountsActions.ActiveUsersCountFetchFinished,
  );

export interface ITeamFetchStartedProps {
  offset?: number;
}
export type TTeamFetchStarted = ITypedReduxAction<EAccountsActions.TeamFetchStarted, ITeamFetchStartedProps>;
export const teamFetchStarted: (payload: ITeamFetchStartedProps) => TTeamFetchStarted =
  actionGenerator<EAccountsActions.TeamFetchStarted, ITeamFetchStartedProps>(EAccountsActions.TeamFetchStarted);

export type TTeamFetchFailed = ITypedReduxAction<EAccountsActions.TeamFetchFailed, void>;
export const teamFetchFailed: (payload?: void) => TTeamFetchFailed =
  actionGenerator<EAccountsActions.TeamFetchFailed, void>(EAccountsActions.TeamFetchFailed);

export type TTeamFetchFinished = ITypedReduxAction<EAccountsActions.TeamFetchFinished, TUserListItem[]>;
export const teamFetchFinished: (payload: TUserListItem[]) => TTeamFetchFinished =
  actionGenerator<EAccountsActions.TeamFetchFinished, TUserListItem[]>(EAccountsActions.TeamFetchFinished);

export type TUserListSortingChanged = ITypedReduxAction<EAccountsActions.UserListSortingChanged, EUserListSorting>;
export const changeUserListSorting: (payload: EUserListSorting) => TUserListSortingChanged =
  actionGenerator<EAccountsActions.UserListSortingChanged, EUserListSorting>(EAccountsActions.UserListSortingChanged);

export type TSetCurrentPlan = ITypedReduxAction<EAccountsActions.SetCurrentPlan, IAccountPlan>;
export const setCurrentPlan: (payload: IAccountPlan) => TSetCurrentPlan =
  actionGenerator<EAccountsActions.SetCurrentPlan, IAccountPlan>(EAccountsActions.SetCurrentPlan);

export interface IChangeUserAdminProps {
  id: number;
  email: string;
  isAdmin: boolean;
}

export type TChangeUserAdmin = ITypedReduxAction<EAccountsActions.ChangeUserAdmin, IChangeUserAdminProps>;
export const changeUserAdmin: (payload: IChangeUserAdminProps) => TChangeUserAdmin =
  actionGenerator<EAccountsActions.ChangeUserAdmin, IChangeUserAdminProps>(EAccountsActions.ChangeUserAdmin);

export type TLoadChangeUserAdmin = ITypedReduxAction<EAccountsActions.LoadChangeUserAdmin, IChangeUserAdminProps>;
export const loadChangeUserAdmin: (payload: IChangeUserAdminProps) => TLoadChangeUserAdmin =
  actionGenerator<EAccountsActions.LoadChangeUserAdmin, IChangeUserAdminProps>(EAccountsActions.LoadChangeUserAdmin);

export type TDeleteUserPayload = {
  userId: number;
  reassignedUserId: number | null;
};
export type TDeleteUser = ITypedReduxAction<EAccountsActions.DeleteUser, TDeleteUserPayload>;
export const deleteUser: (payload: TDeleteUserPayload) => TDeleteUser =
  actionGenerator<EAccountsActions.DeleteUser, TDeleteUserPayload>(EAccountsActions.DeleteUser);

export type TDeclineIvitePayload = {
  userId: number;
  inviteId: string;
  reassignedUserId: number | null;
};
export type TDeclineIvite = ITypedReduxAction<EAccountsActions.DeclineInvite, TDeclineIvitePayload>;
export const declineInvite: (payload: TDeclineIvitePayload) => TDeclineIvite =
  actionGenerator<EAccountsActions.DeclineInvite, TDeclineIvitePayload>(EAccountsActions.DeclineInvite);

export type TOpenDeleteUserModalPayload = {
  user: TUserListItem;
};
export type TOpenDeleteUserModal = ITypedReduxAction<EAccountsActions.OpenDeleteUserModal, TOpenDeleteUserModalPayload>;
export const openDeleteUserModal: (payload: TOpenDeleteUserModalPayload) => TOpenDeleteUserModal =
  actionGenerator<EAccountsActions.OpenDeleteUserModal, TOpenDeleteUserModalPayload>(
    EAccountsActions.OpenDeleteUserModal,
  );

export type TCloseDeleteUserModal = ITypedReduxAction<EAccountsActions.CloseDeleteUserModal, void>;
export const closeDeleteUserModal: (payload?: void) => TCloseDeleteUserModal =
  actionGenerator<EAccountsActions.CloseDeleteUserModal, void>(EAccountsActions.CloseDeleteUserModal);

export type TSetDeleteUserModalState = ITypedReduxAction<
EAccountsActions.SetDeleteUserModalState,
EDeleteUserModalState
>;
export const setDeleteUserModalState: (payload: EDeleteUserModalState) => TSetDeleteUserModalState =
  actionGenerator<EAccountsActions.SetDeleteUserModalState, EDeleteUserModalState>(
    EAccountsActions.SetDeleteUserModalState,
  );

export type TSetWorkflowsCount = ITypedReduxAction<EAccountsActions.SetWorkflowsCount, number>;
export const setUserWorkflowsCount: (payload: number) => TSetWorkflowsCount =
  actionGenerator<EAccountsActions.SetWorkflowsCount, number>(EAccountsActions.SetWorkflowsCount);

export type TFetchPlan = ITypedReduxAction<EAccountsActions.FetchPlan, void>;
export const loadPlan: (payload?: void) => TFetchPlan =
  actionGenerator<EAccountsActions.FetchPlan, void>(EAccountsActions.FetchPlan);

export type TStartTrialSubscription = ITypedReduxAction<EAccountsActions.StartTrialSubscription, void>;
export const startTrialSubscriptionAction: (payload?: void) => TStartTrialSubscription =
  actionGenerator<EAccountsActions.StartTrialSubscription, void>(EAccountsActions.StartTrialSubscription);

export type TStartFreeSubscription = ITypedReduxAction<EAccountsActions.StartFreeSubscription, void>;
export const startFreeSubscriptionAction: (payload?: void) => TStartFreeSubscription =
  actionGenerator<EAccountsActions.StartFreeSubscription, void>(EAccountsActions.StartFreeSubscription);

export type TShowPlanExpiredMessage = ITypedReduxAction<EAccountsActions.ShowPlanExpiredMessage, void>;
export const showPlanExpiredMessage: (payload?: void) => TShowPlanExpiredMessage =
  actionGenerator<EAccountsActions.ShowPlanExpiredMessage, void>(EAccountsActions.ShowPlanExpiredMessage);

export type TAccountsActions =
  TUsersFetchStarted
  | TUsersFetchFailed
  | TUsersFetchFinished
  | TActiveUsersCountFetchStarted
  | TActiveUsersCountFetchFinished
  | TUserListSortingChanged
  | TSetCurrentPlan
  | TFetchCurrentPlanFailed
  | TTeamFetchStarted
  | TTeamFetchFailed
  | TTeamFetchFinished
  | TChangeUserAdmin
  | TResetUsers
  | TDeleteUser
  | TDeclineIvite
  | TOpenDeleteUserModal
  | TCloseDeleteUserModal
  | TSetDeleteUserModalState
  | TSetWorkflowsCount
  | TSetIsLoading
  | TFetchPlan
  | TStartTrialSubscription
  | TStartFreeSubscription
  | TShowPlanExpiredMessage;

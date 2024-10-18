/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count
import { all, call, fork, put, select, takeEvery, takeLatest } from 'redux-saga/effects';
import {
  EAccountsActions,
  teamFetchFailed,
  teamFetchFinished,
  teamFetchStarted,
  fetchCurrentPlanFailed,
  setCurrentPlan,
  usersFetchFailed,
  usersFetchFinished,
  TLoadChangeUserAdmin,
  changeUserAdmin,
  TDeleteUser,
  TOpenDeleteUserModal,
  TDeclineIvite,
  setDeleteUserModalState,
  TCloseDeleteUserModal,
  setUserWorkflowsCount,
  usersFetchStarted,
  activeUsersCountFetchFinished,
  TUsersFetchStarted,
  loadActiveUsersCount,
} from '../actions';

import { getAccountsStore, getSubscriptionPlan } from '../selectors/user';
import { EUserListSorting, EUserStatus, TUserListItem } from '../../types/user';
import { EDeleteUserModalState, IAccounts } from '../../types/redux';

import { getErrorMessage } from '../../utils/getErrorMessage';
import { getUsers, TResponseUser } from '../../api/getUsers';
import { getPlan, TGetPlanResponse } from '../../api/getPlan';
import { authUserSuccess, makeStripePayment, TAuthUserResult } from '../auth/actions';
import { ERoutes } from '../../constants/routes';
import { changeUserPermissions } from '../../api/changeUserPermissions';
import { NotificationManager } from '../../components/UI/Notifications';
import { deleteUser } from '../../api/deleteUser';
import { declineInvite } from '../../api/declineInvite';
import { countUserWorkflows, TCountUserWorkflowsResponse } from '../../api/countUserWorkflows';
import { reassignWorkflows } from '../../api/reassignWorkflows';
import { ESubscriptionPlan } from '../../types/account';
import { logger } from '../../utils/logger';
import { setGeneralLoaderVisibility } from '../general/actions';
import { auth } from '../../api/auth';
import { startFreeSubscription } from '../../api/startFreeSubscription';
import { getActiveUsersCount, IGetActiveUsersCountResponse } from '../../api/getActiveUsersCount';
import { sortUsersByStatus, sortUsersByNameAsc, sortUsersByNameDesc } from '../../utils/users';
import { getAccountPlan } from '../selectors/accounts';
import { getAbsolutePath } from '../../utils/getAbsolutePath';
import { getTenantsCountStore } from '../selectors/tenants';

export function* fetchUsers(
  action: TUsersFetchStarted = {
    type: EAccountsActions.UsersFetchStarted,
    payload: { showErrorNotification: true },
  },
) {
  const { payload: { showErrorNotification } = { showErrorNotification: true } } = action;

  try {
    const userList: TResponseUser[] = yield call(getUsers);

    const normalizedUsers: TUserListItem[] = userList.map((user) => {
      const emptyUserData: TUserListItem = {
        id: -1,
        isAdmin: false,
        isAccountOwner: false,
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        photo: '',
        type: 'user',
        status: EUserStatus.Active,
      };

      return { ...emptyUserData, ...user };
    });

    const sortedUsers = sortUsersByStatus(sortUsersByNameAsc(normalizedUsers));

    yield put(usersFetchFinished(sortedUsers));
  } catch (error) {
    if (showErrorNotification) {
      NotificationManager.error({ title: 'users.faied-fetch', message: getErrorMessage(error) });
    }

    console.info('fetch users error : ', error);
    yield put(usersFetchFailed());
  }
}

export function* fetchActiveUsersCount() {
  try {
    const { activeUsers }: IGetActiveUsersCountResponse = yield call(getActiveUsersCount);
    const tenantCount: number = yield select(getTenantsCountStore);

    yield put(activeUsersCountFetchFinished({ activeUsers, tenantsActiveUsers: tenantCount || 333 }));
  } catch (error) {
    console.info('fetch active users count error : ', error);
  }
}

export function* fetchPlan() {
  const currentPlan: ReturnType<typeof getAccountPlan> = yield select(getAccountPlan);
  try {
    const currentPlan: TGetPlanResponse = yield call(getPlan);
    yield put(setCurrentPlan(currentPlan));
  } catch (error) {
    NotificationManager.error({ title: 'plan.fetch-error', message: getErrorMessage(error) });
    console.info('fetch plan error : ', error);
    yield put(fetchCurrentPlanFailed());
    yield put(
      setCurrentPlan({
        ...currentPlan,
        billingPlan: ESubscriptionPlan.Free,
        planExpiration: null,
      }),
    );
  }
}

function getSortedUsers(users: TUserListItem[], sorting: EUserListSorting) {
  const sortingMethodMap = {
    [EUserListSorting.NameAsc]: sortUsersByNameAsc,
    [EUserListSorting.NameDesc]: sortUsersByNameDesc,
    [EUserListSorting.Status]: (users: TUserListItem[]) => sortUsersByStatus(sortUsersByNameAsc(users)),
  };

  return sortingMethodMap[sorting](users);
}

function* fetchTeam() {
  try {
    const { userListSorting: sorting }: IAccounts = yield select(getAccountsStore);
    const users: TUserListItem[] = yield getUsers({
      type: 'user',
      status: [EUserStatus.Active, EUserStatus.Invited],
    });

    yield put(teamFetchFinished(getSortedUsers(users, sorting)));
  } catch (error) {
    console.info('fetch users error : ', error);
    yield put(teamFetchFailed());
  }
}

function* saveUserAdmin({ payload: { isAdmin, email, id } }: TLoadChangeUserAdmin) {
  try {
    yield put(changeUserAdmin({ isAdmin, email, id }));
    yield changeUserPermissions(id);
  } catch (error) {
    console.info('fetch to toggle admin rights : ', error);
    NotificationManager.warning({
      message: getErrorMessage(error)
    });

    yield put(changeUserAdmin({ isAdmin: !isAdmin, email, id }));
    yield put(teamFetchFailed());
  }
}

async function fetchReassignWorkflows(oldUserId: number, newUserId: number | null) {
  if (!newUserId) {
    return;
  }

  try {
    await reassignWorkflows(oldUserId, newUserId);
  } catch (error) {
    throw error;
  }
}

function* fetchDeleteUser({ payload: { userId, reassignedUserId } }: TDeleteUser) {
  try {
    yield put(setDeleteUserModalState(EDeleteUserModalState.PerformingAction));
    yield call(fetchReassignWorkflows, userId, reassignedUserId);
    yield call(deleteUser, userId);
    NotificationManager.success({ message: 'team.delete-success-msg' });
    yield put(teamFetchStarted({}));
    yield put(usersFetchStarted());
    yield put(loadActiveUsersCount());
  } catch (err) {
    NotificationManager.warning({ message: getErrorMessage(err) });
  } finally {
    yield put(setDeleteUserModalState(EDeleteUserModalState.Closed));
  }
}

function* fetchDeclineInvite({ payload: { userId, inviteId, reassignedUserId } }: TDeclineIvite) {
  try {
    yield put(setDeleteUserModalState(EDeleteUserModalState.PerformingAction));
    yield call(fetchReassignWorkflows, userId, reassignedUserId);
    yield call(declineInvite, inviteId);
    NotificationManager.success({ message: 'team.decline-invite-success-msg' });
    yield put(teamFetchStarted({}));
    yield put(usersFetchStarted());
    yield put(loadActiveUsersCount());
  } catch (err) {
    NotificationManager.warning({ message: getErrorMessage(err) });
  } finally {
    yield put(setDeleteUserModalState(EDeleteUserModalState.Closed));
  }
}

function* handleToggleDeleteUserModal(action: TOpenDeleteUserModal | TCloseDeleteUserModal) {
  if (action.type === EAccountsActions.CloseDeleteUserModal) {
    return;
  }

  const {
    payload: { user },
  } = action;

  try {
    yield put(setDeleteUserModalState(EDeleteUserModalState.FetchingUserData));

    const { count: userWorkflows }: TCountUserWorkflowsResponse = yield call(countUserWorkflows, user.id!);

    yield put(setUserWorkflowsCount(userWorkflows));
    yield put(setDeleteUserModalState(EDeleteUserModalState.WaitingForAction));
  } catch (err) {
    yield put(setDeleteUserModalState(EDeleteUserModalState.Closed));
    NotificationManager.warning({ message: 'team.fetch-user-error' });
  }
}

function* onChangeUserSorting() {
  const {
    userListSorting: sorting,
    team: { list: users },
  }: IAccounts = yield select(getAccountsStore);

  yield put(teamFetchFinished(getSortedUsers(users, sorting)));
}

function* startTrialSubscriptionSaga() {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield put(
      makeStripePayment({
        successUrl: getAbsolutePath(ERoutes.AfterPaymentDetailsProvided, { trial_started: 'true' }),
        cancelUrl: getAbsolutePath(ERoutes.Tasks),
        code: 'unlimited_month',
      }),
    );
  } catch (error) {
    const message = getErrorMessage(error);
    NotificationManager.error({ message });
    logger.error(`failed to start trial subscription: ${message}`);
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* startFreeSubscriptionSaga() {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield startFreeSubscription();

    yield fetchPlan();
    const result: TAuthUserResult = yield call(auth.getUser);
    yield put(authUserSuccess(result));
    NotificationManager.success({ message: 'pricing.switched-to-free-plan' });
  } catch (error) {
    const message = getErrorMessage(error);
    NotificationManager.error({ message });
    logger.error(`failed to start free subscription: ${message}`);
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* showPlanExpiredMessageSaga() {
  const subscriptionPlan: ReturnType<typeof getSubscriptionPlan> = yield select(getSubscriptionPlan);
  const messagesMap = {
    [ESubscriptionPlan.Unknown]: '',
    [ESubscriptionPlan.Free]: '',
    [ESubscriptionPlan.Trial]: 'general.trial-expired',
    [ESubscriptionPlan.Premium]: 'general.premium-expired',
    [ESubscriptionPlan.Unlimited]: 'general.premium-expired',
    [ESubscriptionPlan.FractionalCOO]: 'general.premium-expired',
  };
  const message = messagesMap[subscriptionPlan];

  NotificationManager.error({ message });
}

export function* watchFetchUser() {
  yield takeEvery(EAccountsActions.UsersFetchStarted, fetchUsers);
}

export function* watchFetchActiveUsersCount() {
  yield takeEvery(EAccountsActions.ActiveUsersCountFetchStarted, fetchActiveUsersCount);
}

export function* watchFetchTeam() {
  yield takeEvery(EAccountsActions.TeamFetchStarted, fetchTeam);
}

export function* watchUserListSortingChnaged() {
  yield takeEvery(EAccountsActions.UserListSortingChanged, onChangeUserSorting);
}

export function* watchChangeAdminUser() {
  yield takeEvery(EAccountsActions.LoadChangeUserAdmin, saveUserAdmin);
}

export function* watchOpenDeleteUserModal() {
  yield takeLatest(
    [EAccountsActions.OpenDeleteUserModal, EAccountsActions.CloseDeleteUserModal],
    handleToggleDeleteUserModal,
  );
}

export function* watchDeleteUser() {
  yield takeEvery(EAccountsActions.DeleteUser, fetchDeleteUser);
}

export function* watchDeclineInvite() {
  yield takeEvery(EAccountsActions.DeclineInvite, fetchDeclineInvite);
}

export function* watchFetchPlan() {
  yield takeEvery(EAccountsActions.FetchPlan, fetchPlan);
}

export function* watchStartTrialSubscription() {
  yield takeEvery(EAccountsActions.StartTrialSubscription, startTrialSubscriptionSaga);
}

export function* watchStartFreeSubscription() {
  yield takeEvery(EAccountsActions.StartFreeSubscription, startFreeSubscriptionSaga);
}

export function* watchShowPlanExpiredMessage() {
  yield takeEvery(EAccountsActions.ShowPlanExpiredMessage, showPlanExpiredMessageSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchUser),
    fork(watchFetchActiveUsersCount),
    fork(watchUserListSortingChnaged),
    fork(watchFetchTeam),
    fork(watchChangeAdminUser),
    fork(watchOpenDeleteUserModal),
    fork(watchDeleteUser),
    fork(watchDeclineInvite),
    fork(watchFetchPlan),
    fork(watchStartTrialSubscription),
    fork(watchStartFreeSubscription),
    fork(watchShowPlanExpiredMessage),
  ]);
}

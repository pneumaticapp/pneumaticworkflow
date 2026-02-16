import { all, call, fork, put, select, takeEvery, takeLatest } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';
import {
  teamFetchFailed,
  teamFetchFinished,
  teamFetchStarted,
  fetchCurrentPlanFailed,
  setCurrentPlan,
  usersFetchFailed,
  usersFetchFinished,
  changeUserAdmin,
  setDeleteUserModalState,
  setWorkflowsCount as setUserWorkflowsCount,
  usersFetchStarted,
  activeUsersCountFetchFinished,
  loadActiveUsersCount,
  closeCreateUserModal,
  closeDeleteUserModal,
  openDeleteUserModal,
  userListSortingChanged,
  loadChangeUserAdmin,
  deleteUser as deleteUserAction,
  declineInvite as declineInviteAction,
  loadPlan,
  startTrialSubscriptionAction,
  startFreeSubscriptionAction,
  createUser,
} from './slice';

import {
  IChangeUserAdminProps,
  TOpenDeleteUserModalPayload,
  TDeleteUserPayload,
  TUsersFetchPayload,
  TDeclineInvitePayload,
} from './types';

import { getAccountsStore } from '../selectors/user';
import { EUserListSorting, EUserStatus, ICreateUserRequest, TUserListItem } from '../../types/user';
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
import { createUser as createUserApi } from '../../api/createUser';

export function* fetchUsers(
  action: PayloadAction<TUsersFetchPayload> = { type: 'accounts/usersFetchStarted', payload: { showErrorNotification: true } }
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
      NotificationManager.notifyApiError(error, { title: 'users.faied-fetch', message: getErrorMessage(error) });
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
    const planResponse: TGetPlanResponse = yield call(getPlan);
    yield put(setCurrentPlan(planResponse));
  } catch (error) {
    NotificationManager.notifyApiError(error, { title: 'plan.fetch-error', message: getErrorMessage(error) });
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
    [EUserListSorting.Status]: (usersList: TUserListItem[]) => sortUsersByStatus(sortUsersByNameAsc(usersList)),
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

function* saveUserAdmin({ payload: { isAdmin, email, id } }: PayloadAction<IChangeUserAdminProps>) {
  try {
    yield put(changeUserAdmin({ isAdmin, email, id }));
    yield changeUserPermissions(id);
  } catch (error) {
    console.info('fetch to toggle admin rights : ', error);
    NotificationManager.warning({
      message: getErrorMessage(error),
    });

    yield put(changeUserAdmin({ isAdmin: !isAdmin, email, id }));
    yield put(teamFetchFailed());
  }
}

async function fetchReassignWorkflows(oldUserId: number, newUserId: number | null) {
  if (!newUserId) {
    return;
  }

  await reassignWorkflows(oldUserId, newUserId);
}

function* fetchDeleteUser({ payload: { userId, reassignedUserId } }: PayloadAction<TDeleteUserPayload>) {
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

function* fetchDeclineInvite({ payload: { userId, inviteId, reassignedUserId } }: PayloadAction<TDeclineInvitePayload>) {
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

function* handleToggleDeleteUserModal(action: PayloadAction<TOpenDeleteUserModalPayload> | PayloadAction<void>) {
  if (action.type === 'accounts/closeDeleteUserModal') {
    return;
  }

  const {
    payload: { user },
  } = action as PayloadAction<TOpenDeleteUserModalPayload>;

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
    NotificationManager.notifyApiError(error, { message });
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
    NotificationManager.notifyApiError(error, { message });
    logger.error(`failed to start free subscription: ${message}`);
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* createUserSaga({ payload }: PayloadAction<ICreateUserRequest>) {
  try {
    yield call(createUserApi, payload);
    NotificationManager.success({ message: 'team.create-user-success-msg' });
    yield put(closeCreateUserModal());

    yield put(teamFetchStarted({}));
    yield put(usersFetchStarted());
    yield put(loadActiveUsersCount());
  } catch (error) {
    NotificationManager.notifyApiError( error, { message: getErrorMessage(error) });
    logger.error('failed to create user', error);
  }
}

export function* watchFetchUser() {
  yield takeEvery(usersFetchStarted.type, fetchUsers);
}

export function* watchFetchActiveUsersCount() {
  yield takeEvery(loadActiveUsersCount.type, fetchActiveUsersCount);
}

export function* watchFetchTeam() {
  yield takeEvery(teamFetchStarted.type, fetchTeam);
}

export function* watchUserListSortingChnaged() {
  yield takeEvery(userListSortingChanged.type, onChangeUserSorting);
}

export function* watchChangeAdminUser() {
  yield takeEvery(loadChangeUserAdmin.type, saveUserAdmin);
}

export function* watchOpenDeleteUserModal() {
  yield takeLatest(
    [openDeleteUserModal.type, closeDeleteUserModal.type],
    handleToggleDeleteUserModal,
  );
}

export function* watchDeleteUser() {
  yield takeEvery(deleteUserAction.type, fetchDeleteUser);
}

export function* watchDeclineInvite() {
  yield takeEvery(declineInviteAction.type, fetchDeclineInvite);
}

export function* watchFetchPlan() {
  yield takeEvery(loadPlan.type, fetchPlan);
}

export function* watchStartTrialSubscription() {
  yield takeEvery(startTrialSubscriptionAction.type, startTrialSubscriptionSaga);
}

export function* watchStartFreeSubscription() {
  yield takeEvery(startFreeSubscriptionAction.type, startFreeSubscriptionSaga);
}

export function* watchCreateUser() {
  yield takeEvery(createUser.type, createUserSaga);
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
    fork(watchCreateUser),
  ]);
}

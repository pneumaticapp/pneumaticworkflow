import { all, fork, takeEvery, put, select, takeLatest } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';
import { InviteResponse, sendInvites } from '../../api/sendInvites';
import { NotificationManager } from '../../components/UI/Notifications';
import { TUserListItem } from '../../types/user';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { history } from '../../utils/history';
import { logger } from '../../utils/logger';
import { showInvitesNotification } from '../../utils/users';
import { fetchUsers } from '../accounts/saga';
import { loadActiveUsersCount , teamFetchStarted } from '../accounts/slice';

import { setGeneralLoaderVisibility } from '../general/actions';
import { getUsers } from '../selectors/user';
import { getInvites } from '../../api/team/getInvites';
import { ERoutes } from '../../constants/routes';
import { TeamPages, TInviteUsersPayload, UserInvite } from './types';
import { 
  changeTeamActiveTab, 
  inviteUsers, 
  loadInvitesUsers, 
  loadInvitesUsersSuccess, 
  setRecentInvitedUsers, 
  setTeamActivePage 
} from './slice';



function* inviteUsersSaga({
  payload: { invites, withGeneralLoader, withSuccessNotification, onStartUploading, onEndUploading, onError },
}: PayloadAction<TInviteUsersPayload>) {
  try {
    onStartUploading?.();
    if (withGeneralLoader) {
      yield put(setGeneralLoaderVisibility(true));
    }

    const sendInvitesResult: InviteResponse | undefined = yield sendInvites(invites, history.location.pathname);
    yield fetchUsers();

    if (!sendInvitesResult) {
      return;
    }

    if (withSuccessNotification) {
      showInvitesNotification({ invites, sendInvitesResult });
    }

    const users: ReturnType<typeof getUsers> = yield select(getUsers);
    const recentInvitedUsers: TUserListItem[] = users.filter((userData) =>
      invites.some((invitedUserData) => invitedUserData.email === userData.email),
    );

    yield put(setRecentInvitedUsers(recentInvitedUsers));
    yield put(teamFetchStarted({}));
    yield put(loadActiveUsersCount());

    onEndUploading?.();
  } catch (err) {
    NotificationManager.warning({ message: getErrorMessage(err) });
    onError?.();
    logger.error('failed to send ivites', err);
  } finally {
    if (withGeneralLoader) {
      yield put(setGeneralLoaderVisibility(false));
    }
  }
}

function* loadInvitesUsersSaga() {
  try {
    const invites: UserInvite[] = yield getInvites();

    yield put(loadInvitesUsersSuccess(invites));
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load invites users', error);
  }
}

function* setTeamActiveTab({ payload: processesType }: PayloadAction<TeamPages>) {
  yield put(changeTeamActiveTab(processesType));

  if (processesType === TeamPages.Groups) {
    history.push(ERoutes.Groups);
  }

  if (processesType === TeamPages.Users) {
    history.push(ERoutes.Team);
  }
}

export function* watchSetProcessTypeSorting() {
  yield takeLatest(setTeamActivePage.type, setTeamActiveTab);
}

export function* watchInviteUsers() {
  yield takeEvery(inviteUsers.type, inviteUsersSaga);
}

export function* watchLoadInvitesUsers() {
  yield takeEvery(loadInvitesUsers.type, loadInvitesUsersSaga);
}

export function* rootSaga() {
  yield all([fork(watchInviteUsers), fork(watchLoadInvitesUsers), fork(watchSetProcessTypeSorting)]);
}

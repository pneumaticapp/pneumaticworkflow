import { all, fork, takeEvery, put, select, takeLatest } from 'redux-saga/effects';
import { InviteResponse, sendInvites } from '../../api/sendInvites';
import { NotificationManager } from '../../components/UI/Notifications';
import { TUserListItem } from '../../types/user';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { history } from '../../utils/history';
import { logger } from '../../utils/logger';
import { showInvitesNotification } from '../../utils/users';
import { fetchUsers } from '../accounts/saga';
import { loadActiveUsersCount, teamFetchStarted } from '../actions';
import { setGeneralLoaderVisibility } from '../general/actions';
import { getUsers } from '../selectors/user';
import {
  changeTeamActiveTab,
  ETeamActions,
  loadInvitesUsersSuccess,
  setRecentInvitedUsers,
  TInviteUsers,
  TSetTeamActivePage,
} from './actions';
import { ETeamPages, UserInvite } from '../../types/team';
import { getInvites } from '../../api/team/getInvites';
import { ERoutes } from '../../constants/routes';

function* inviteUsersSaga({
  payload: { invites, withGeneralLoader, withSuccessNotification, onStartUploading, onEndUploading, onError },
}: TInviteUsers) {
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

function* setTeamActiveTab({ payload: processesType }: TSetTeamActivePage) {
  yield put(changeTeamActiveTab(processesType));

  if (processesType === ETeamPages.Groups) {
    history.push(ERoutes.Groups);
  }

  if (processesType === ETeamPages.Users) {
    history.push(ERoutes.Team);
  }
}

export function* watchSetProcessTypeSorting() {
  yield takeLatest(ETeamActions.SetTeamActivePage, setTeamActiveTab);
}

export function* watchInviteUsers() {
  yield takeEvery(ETeamActions.InviteUsers, inviteUsersSaga);
}

export function* watchLoadInvitesUsers() {
  yield takeEvery(ETeamActions.LoadInvitesUsers, loadInvitesUsersSaga);
}

export function* rootSaga() {
  yield all([fork(watchInviteUsers), fork(watchLoadInvitesUsers), fork(watchSetProcessTypeSorting)]);
}

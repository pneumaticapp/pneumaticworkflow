import { all, fork, takeEvery, put, select } from 'redux-saga/effects';
import { IInviteResponse, sendInvites } from '../../api/sendInvites';
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
import { ETeamActions, loadMicrosoftInvitesSuccess, setRecentInvitedUsers, TInviteUsers } from './actions';
import { IUserInviteMicrosoft } from '../../types/team';
import { getInvites } from '../../api/team/getInvites';

function* inviteUsersSaga({
  payload: { invites, withGeneralLoader, withSuccessNotification, onStartUploading, onEndUploading, onError },
}: TInviteUsers) {
  try {
    onStartUploading?.();
    if (withGeneralLoader) {
      yield put(setGeneralLoaderVisibility(true));
    }

    const sendInvitesResult: IInviteResponse | undefined = yield sendInvites(invites, history.location.pathname);
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

function* loadMicrosoftInvitesSaga() {
  try {
    const invites: IUserInviteMicrosoft[] = yield getInvites();

    yield put(loadMicrosoftInvitesSuccess(invites));
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load microsoft invites', error);
  }
}

export function* watchInviteUsers() {
  yield takeEvery(ETeamActions.InviteUsers, inviteUsersSaga);
}

export function* watchLoadMicrosoftInvites() {
  yield takeEvery(ETeamActions.LoadMicrosoftInvites, loadMicrosoftInvitesSaga);
}

export function* rootSaga() {
  yield all([fork(watchInviteUsers), fork(watchLoadMicrosoftInvites)]);
}

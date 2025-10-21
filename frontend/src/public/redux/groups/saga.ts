import { all, fork, takeEvery, put, select, debounce } from 'redux-saga/effects';

import { getErrorMessage } from '../../utils/getErrorMessage';

import { logger } from '../../utils/logger';
import { history } from '../../utils/history';
import {
  EGroupsActions,
  loadGroupsSuccess,
  loadGroupSuccess,
  TCreateGroup,
  TDeleteGroup,
  TUpdateGroup,
  updateGroupSuccess,
} from '../actions';
import { getGroups } from '../../api/team/getGroups';
import { createGroup } from '../../api/team/createGroup';
import { deleteGroup } from '../../api/team/deleteGroup';
import { NotificationManager } from '../../components/UI/Notifications';
import { getGroupsStore } from '../selectors/user';
import { IGroupsStore } from '../../types/redux';
import { updateGroupApi } from '../../api/team/updateGroupApi';
import { getGroup } from '../../api/team/getGroup';
import { ERoutes } from '../../constants/routes';
import { EResponseStatuses } from '../../constants/defaultValues';
import { IGroup } from '../team/types';



function* loadGroupsSaga() {
  try {
    yield fetchGroupsSaga();
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load groups', error);
  }
}

function* fetchGroupsSaga() {
  try {
    const { groupsListSorting: sorting }: IGroupsStore = yield select(getGroupsStore);
    const groups: IGroup[] = yield getGroups({ ordering: sorting });

    yield put(loadGroupsSuccess(groups));
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to fetch groups', error);
  }
}

function* groupsListSortingChangedSaga() {
  yield fetchGroupsSaga();
}

function* createGroupSaga({ payload }: TCreateGroup) {
  try {
    yield createGroup(payload);
    yield fetchGroupsSaga();
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create group', error);
  }
}

function* updateGroupSaga({ payload }: TUpdateGroup) {
  try {
    const group: IGroup = yield updateGroupApi(payload);

    yield put(updateGroupSuccess(group));
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update group', error);
  }
}

function* deleteGroupSaga({ payload }: TDeleteGroup) {
  try {
    yield deleteGroup(payload);
    yield fetchGroupsSaga();
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete group', error);
  }
}

function* loadGroupSaga({ payload }: any) {
  try {
    const group: IGroup = yield getGroup(payload);
    yield put(loadGroupSuccess(group));
  } catch (error) {
    const isGroupNotFound = error?.status === EResponseStatuses.NotFound;
    if (isGroupNotFound) {
      history.replace(ERoutes.Error);

      return;
    }
    history.replace(ERoutes.Error);
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load group', error);
  }
}

export function* watchLoadGroup() {
  yield takeEvery(EGroupsActions.LoadGroup, loadGroupSaga);
}

export function* watchLoadGroups() {
  yield takeEvery(EGroupsActions.LoadGroups, loadGroupsSaga);
}

export function* watchCreateGroup() {
  yield takeEvery(EGroupsActions.CreateGroup, createGroupSaga);
}

export function* watchDeleteGroup() {
  yield takeEvery(EGroupsActions.DeleteGroup, deleteGroupSaga);
}

export function* watchGroupsListSortingChanged() {
  yield takeEvery(EGroupsActions.GroupsListSortingChanged, groupsListSortingChangedSaga);
}

export function* watchUpdateGroup() {
  yield takeEvery(EGroupsActions.UpdateGroup, updateGroupSaga);
}

export function* watchUpdateUsersGroup() {
  yield debounce(1000, EGroupsActions.UpdateUsersGroup, updateGroupSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadGroups),
    fork(watchCreateGroup),
    fork(watchLoadGroup),
    fork(watchDeleteGroup),
    fork(watchUpdateUsersGroup),
    fork(watchUpdateGroup),
    fork(watchGroupsListSortingChanged),
  ]);
}

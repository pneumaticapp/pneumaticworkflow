import { all, fork, takeEvery, put, select, debounce } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { getRouteParamId, history } from '../../utils/history';
import { getGroups } from '../../api/team/getGroups';
import { createGroup as createGroupApi } from '../../api/team/createGroup';
import { deleteGroup as deleteGroupApi } from '../../api/team/deleteGroup';
import { NotificationManager } from '../../components/UI/Notifications';
import { getGroupsStore } from '../selectors/user';
import { IGroupsStore } from '../../types/redux';
import { updateGroupApi } from '../../api/team/updateGroupApi';
import { getGroup } from '../../api/team/getGroup';
import { ERoutes } from '../../constants/routes';
import { EResponseStatuses } from '../../constants/defaultValues';
import { IGroup } from '../team/types';

import {
  loadGroups,
  createGroup,
  updateGroup,
  updateUsersGroup,
  deleteGroup,
  loadGroup,
  loadGroupsSuccess,
  loadGroupSuccess,
  createGroupFailed,
  updateGroupFailed,
  updateGroupSuccess,
  groupsListSortingChanged,
  removeGroupFromWs,
  resetGroup,
} from './slice';

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

function* createGroupSaga({ payload }: PayloadAction<IGroup>) {
  try {
    yield createGroupApi(payload);
    yield fetchGroupsSaga();
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create group', error);
    yield put(createGroupFailed());
  }
}

function* restoreGroupFromServer(groupId: number) {
  try {
    const group: IGroup = yield getGroup(groupId as unknown as Pick<IGroup, 'id'>);
    yield put(updateGroupSuccess(group));
  } catch (error) {
    logger.error('failed to restore group after update error', error);
  }
}

function* updateGroupSaga({ payload, type }: PayloadAction<IGroup>) {
  try {
    const group: IGroup = yield updateGroupApi(payload);

    yield put(updateGroupSuccess(group));
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update group', error);
    yield put(updateGroupFailed());

    if (type === updateUsersGroup.type) {
      yield restoreGroupFromServer(payload.id);
    }
  }
}

function* deleteGroupSaga({ payload }: PayloadAction<Pick<IGroup, 'id'>>) {
  try {
    yield deleteGroupApi(payload);
    yield fetchGroupsSaga();
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete group', error);
  }
}

function* handleGroupRemovedFromWs({ payload: groupId }: PayloadAction<number>) {
  const openGroupId = getRouteParamId(ERoutes.GroupDetails);
  if (openGroupId !== groupId) {
    return;
  }

  yield put(resetGroup());
  history.replace(ERoutes.Groups);
}

function* loadGroupSaga({ payload }: PayloadAction<number>) {
  try {
    const group: IGroup = yield getGroup(payload as unknown as Pick<IGroup, 'id'>);
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
  yield takeEvery(loadGroup.type, loadGroupSaga);
}

export function* watchLoadGroups() {
  yield takeEvery(loadGroups.type, loadGroupsSaga);
}

export function* watchCreateGroup() {
  yield takeEvery(createGroup.type, createGroupSaga);
}

export function* watchDeleteGroup() {
  yield takeEvery(deleteGroup.type, deleteGroupSaga);
}

export function* watchGroupsListSortingChanged() {
  yield takeEvery(groupsListSortingChanged.type, groupsListSortingChangedSaga);
}

export function* watchUpdateGroup() {
  yield takeEvery(updateGroup.type, updateGroupSaga);
}

export function* watchUpdateUsersGroup() {
  yield debounce(1000, updateUsersGroup.type, updateGroupSaga);
}

export function* watchRemoveGroupFromWs() {
  yield takeEvery(removeGroupFromWs.type, handleGroupRemovedFromWs);
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
    fork(watchRemoveGroupFromWs),
  ]);
}

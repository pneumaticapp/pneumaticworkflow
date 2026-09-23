import { all, fork, put, select, takeEvery } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import { getUserObjectPermissions } from '../../api/getUserObjectPermissions';
import { IObjectPermissionResponseItem } from '../../types/permissions';
import { logger } from '../../utils/logger';
import { getPermissionsUserId } from '../selectors/permissions';

import { loadObjectPermissions, setObjectPermissions } from './slice';
import { ILoadObjectPermissionsPayload } from './types';

export function* fetchObjectPermissions({
  payload: { objType, objIds },
}: PayloadAction<ILoadObjectPermissionsPayload>) {
  const uniqueIds = [...new Set(objIds)];

  // The API rejects an empty obj_ids list.
  if (!uniqueIds.length) {
    return;
  }

  try {
    const requestedByUserId: number | null = yield select(getPermissionsUserId);
    const permissions: IObjectPermissionResponseItem[] = yield getUserObjectPermissions({
      objType,
      objIds: uniqueIds,
    });

    // Supermode/tenant switch may have replaced the user mid-flight; the answer is not theirs.
    const currentUserId: number | null = yield select(getPermissionsUserId);

    if (currentUserId !== requestedByUserId) {
      return;
    }

    yield put(setObjectPermissions({ objType, permissions }));
  } catch (error) {
    // Silent on purpose: the list itself has loaded, only the controls stay hidden.
    logger.error('failed to load object permissions', error);
  }
}

export function* watchLoadObjectPermissions() {
  yield takeEvery(loadObjectPermissions.type, fetchObjectPermissions);
}

export function* rootSaga() {
  yield all([fork(watchLoadObjectPermissions)]);
}

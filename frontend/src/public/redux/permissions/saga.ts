import { all, fork, put, takeEvery } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import { getUserObjectPermissions } from '../../api/getUserObjectPermissions';
import { IObjectPermissionResponseItem } from '../../types/permissions';
import { logger } from '../../utils/logger';

import { ILoadObjectPermissionsPayload, loadObjectPermissions, setObjectPermissions } from './slice';

export function* fetchObjectPermissions({
  payload: { objType, objIds },
}: PayloadAction<ILoadObjectPermissionsPayload>) {
  const uniqueIds = [...new Set(objIds)];

  // The API rejects an empty obj_ids list, and an empty page has nothing to ask about anyway.
  if (!uniqueIds.length) {
    return;
  }

  try {
    const permissions: IObjectPermissionResponseItem[] = yield getUserObjectPermissions({
      objType,
      objIds: uniqueIds,
    });
    yield put(setObjectPermissions({ objType, permissions }));
  } catch (error) {
    // Deliberately silent in the UI: the list itself has loaded, only the controls stay hidden.
    logger.error('failed to load object permissions', error);
  }
}

export function* watchLoadObjectPermissions() {
  yield takeEvery(loadObjectPermissions.type, fetchObjectPermissions);
}

export function* rootSaga() {
  yield all([fork(watchLoadObjectPermissions)]);
}

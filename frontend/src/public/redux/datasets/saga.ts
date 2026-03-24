import { all, fork, put, takeEvery, takeLatest } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { history } from '../../utils/history';
import { ERoutes } from '../../constants/routes';

import { IDataset, IGetDatasetsResponse, ICreateDatasetParams, IUpdateDatasetParams } from '../../types/dataset';
import { TDeleteDatasetPayload } from './types';
import { CLONE_SUFFIX } from './constants';
import { getDatasets } from '../../api/datasets/getDatasets';
import { getDataset } from '../../api/datasets/getDataset';
import { createDataset } from '../../api/datasets/createDataset';
import { updateDataset } from '../../api/datasets/updateDataset';
import { deleteDataset } from '../../api/datasets/deleteDataset';

import {
  loadDatasets,
  loadDatasetsSuccess,
  loadDatasetsFailed,
  loadDataset,
  loadDatasetSuccess,
  loadDatasetFailed,
  setCurrentDataset,
  createDatasetAction,
  cloneDatasetAction,
  updateDatasetAction,
  deleteDatasetAction,
} from './slice';

function* loadDatasetsSaga() {
  try {
    const data: IGetDatasetsResponse = yield getDatasets();
    yield put(loadDatasetsSuccess(data.results));
  } catch (error) {
    yield put(loadDatasetsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load datasets', error);
  }
}

function* loadDatasetSaga({ payload: { id } }: PayloadAction<{ id: number }>) {
  try {
    const currentDataset: IDataset = yield getDataset({ id });
    yield put(loadDatasetSuccess(currentDataset));
  } catch (error) {
    yield put(loadDatasetFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load dataset', error);
  }
}

function* createDatasetSaga({ payload }: PayloadAction<ICreateDatasetParams>) {
  try {
    const createdDataset: IDataset = yield createDataset(payload);
    yield put(loadDatasetSuccess(createdDataset));
    history.push(ERoutes.DatasetDetail.replace(':id', String(createdDataset.id)));
  } catch (error) {
    yield put(loadDatasetsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create dataset', error);
  }
}

function* cloneDatasetSaga({ payload: { id } }: PayloadAction<{ id: number }>) {
  try {
    const originalDataset: IDataset = yield getDataset({ id });

    const clonedDataset: IDataset = yield createDataset({
      name: `${originalDataset.name} ${CLONE_SUFFIX}`,
      description: originalDataset.description,
      items: originalDataset.items.map((item) => ({ value: item.value, order: item.order })),
    });

    yield put(loadDatasetSuccess(clonedDataset));
    history.push(ERoutes.DatasetDetail.replace(':id', String(clonedDataset.id)));
  } catch (error) {
    yield put(loadDatasetsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to clone dataset', error);
  }
}

function* updateDatasetSaga({ payload }: PayloadAction<IUpdateDatasetParams>) {
  try {
    const updatedDataset: IDataset = yield updateDataset(payload);
    yield put(setCurrentDataset(updatedDataset));
  } catch (error) {
    yield put(loadDatasetFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update dataset', error);
  }
}

function* deleteDatasetSaga({ payload: { id, onSuccess } }: PayloadAction<TDeleteDatasetPayload>) {
  try {
    yield deleteDataset({ id });
    yield put(loadDatasets());
    onSuccess?.();
  } catch (error) {
    yield put(loadDatasetsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete dataset', error);
  }
}

function* watchLoadDatasets() {
  yield takeLatest(loadDatasets.type, loadDatasetsSaga);
}

function* watchLoadDataset() {
  yield takeLatest(loadDataset.type, loadDatasetSaga);
}

function* watchCreateDataset() {
  yield takeEvery(createDatasetAction.type, createDatasetSaga);
}

function* watchCloneDataset() {
  yield takeEvery(cloneDatasetAction.type, cloneDatasetSaga);
}

function* watchUpdateDataset() {
  yield takeLatest(updateDatasetAction.type, updateDatasetSaga);
}

function* watchDeleteDataset() {
  yield takeEvery(deleteDatasetAction.type, deleteDatasetSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadDatasets),
    fork(watchLoadDataset),
    fork(watchCreateDataset),
    fork(watchCloneDataset),
    fork(watchUpdateDataset),
    fork(watchDeleteDataset),
  ]);
}

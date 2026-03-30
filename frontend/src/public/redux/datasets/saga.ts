import { all, fork, put, takeEvery, takeLatest, select } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import uniqBy from 'lodash.uniqby';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { history } from '../../utils/history';
import { ERoutes } from '../../constants/routes';

import { IDataset, IGetDatasetsResponse, ICreateDatasetParams, IUpdateDatasetParams } from '../../types/dataset';
import { TDeleteDatasetPayload } from './types';
import { CLONE_SUFFIX } from './constants';
import { LIMIT_LOAD_DATASETS } from '../../constants/defaultValues';
import { getDatasetsStore } from '../selectors/datasets';
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
  removeDatasetFromList,
} from './slice';

function* loadDatasetsSaga({ payload: offset = 0 }: ReturnType<typeof loadDatasets>) {
  try {
    const datasetsStore: ReturnType<typeof getDatasetsStore> = yield select(getDatasetsStore);
    const { datasetsList, datasetsListSorting } = datasetsStore;

    const data: IGetDatasetsResponse = yield getDatasets({
      offset: offset * LIMIT_LOAD_DATASETS,
      limit: LIMIT_LOAD_DATASETS,
      ordering: datasetsListSorting,
    });
    
    const results = data.results || [];
    const count = data.count || 0;

    const items = offset > 0 ? uniqBy([...datasetsList.items, ...results], 'id') : results;

    yield put(loadDatasetsSuccess({ count, offset, items }));
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
    yield put(removeDatasetFromList(id));
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

import { all, call, fork, put, takeEvery, takeLatest, select } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import uniqBy from 'lodash.uniqby';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { history } from '../../utils/history';
import { ERoutes } from '../../constants/routes';
import { isRequestCanceled } from '../../utils/isRequestCanceled';

import {
  IFieldsetTemplate, IGetFieldsetsResponse,
  ICreateFieldsetParams, IUpdateFieldsetParams,
} from '../../types/fieldset';
import { TDeleteFieldsetPayload } from './types';
import { LIMIT_LOAD_FIELDSETS } from '../../constants/defaultValues';
import { getFieldsetsStore } from '../selectors/fieldsets';
import { getFieldsets } from '../../api/fieldsets/getFieldsets';
import { getFieldset } from '../../api/fieldsets/getFieldset';
import { createFieldset } from '../../api/fieldsets/createFieldset';
import { updateFieldset } from '../../api/fieldsets/updateFieldset';
import { deleteFieldset } from '../../api/fieldsets/deleteFieldset';

import {
  loadFieldsets,
  loadFieldsetsSuccess,
  loadFieldsetsFailed,
  loadCurrentFieldset,
  loadCurrentFieldsetSuccess,
  loadCurrentFieldsetFailed,
  setCurrentFieldset,
  createFieldsetAction,
  updateFieldsetAction,
  deleteFieldsetAction,
  removeFieldsetFromList,
} from './slice';

function* loadFieldsetsSaga({ payload: offset = 0 }: ReturnType<typeof loadFieldsets>) {
  const abortController = new AbortController();

  try {
    const fieldsetsStore: ReturnType<typeof getFieldsetsStore> = yield select(getFieldsetsStore);
    const { fieldsetsList, fieldsetsListSorting } = fieldsetsStore;

    const data: IGetFieldsetsResponse = yield call(getFieldsets, {
      offset: offset * LIMIT_LOAD_FIELDSETS,
      limit: LIMIT_LOAD_FIELDSETS,
      ordering: fieldsetsListSorting,
      signal: abortController.signal,
    });

    const results = data.results || [];
    const count = data.count || 0;

    const items = offset > 0 ? uniqBy([...fieldsetsList.items, ...results], 'id') : results;

    yield put(loadFieldsetsSuccess({ count, offset, items }));
  } catch (error) {
    if (isRequestCanceled(error)) return;
    yield put(loadFieldsetsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load fieldsets', error);
  } finally {
    abortController.abort();
  }
}

function* loadCurrentFieldsetSaga({ payload: { id } }: PayloadAction<{ id: number }>) {
  const abortController = new AbortController();

  try {
    const currentFieldset: IFieldsetTemplate = yield call(getFieldset, { id, signal: abortController.signal });
    yield put(loadCurrentFieldsetSuccess(currentFieldset));
  } catch (error) {
    if (isRequestCanceled(error)) return;
    yield put(loadCurrentFieldsetFailed());
    history.push(ERoutes.Fieldsets);
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load current fieldset', error);
  } finally {
    abortController.abort();
  }
}

function* createFieldsetSaga({ payload }: PayloadAction<ICreateFieldsetParams>) {
  try {
    const createdFieldset: IFieldsetTemplate = yield createFieldset(payload);
    yield put(loadCurrentFieldsetSuccess(createdFieldset));
    history.push(ERoutes.FieldsetDetail.replace(':id', String(createdFieldset.id)));
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create fieldset', error);
  }
}

function* updateFieldsetSaga({ payload }: PayloadAction<IUpdateFieldsetParams>) {
  const abortController = new AbortController();

  try {
    const updatedFieldset: IFieldsetTemplate = yield call(updateFieldset, { ...payload, signal: abortController.signal });
    yield put(setCurrentFieldset(updatedFieldset));
  } catch (error) {
    if (isRequestCanceled(error)) return;
    yield put(loadCurrentFieldsetFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update fieldset', error);
  } finally {
    abortController.abort();
  }
}

function* deleteFieldsetSaga({ payload: { id, onSuccess } }: PayloadAction<TDeleteFieldsetPayload>) {
  try {
    yield deleteFieldset({ id });
    yield put(removeFieldsetFromList(id));
    onSuccess?.();
  } catch (error) {
    yield put(loadFieldsetsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete fieldset', error);
  }
}

function* watchLoadFieldsets() {
  yield takeLatest(loadFieldsets.type, loadFieldsetsSaga);
}

function* watchLoadCurrentFieldset() {
  yield takeLatest(loadCurrentFieldset.type, loadCurrentFieldsetSaga);
}

function* watchCreateFieldset() {
  yield takeEvery(createFieldsetAction.type, createFieldsetSaga);
}

function* watchUpdateFieldset() {
  yield takeLatest(updateFieldsetAction.type, updateFieldsetSaga);
}

function* watchDeleteFieldset() {
  yield takeEvery(deleteFieldsetAction.type, deleteFieldsetSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadFieldsets),
    fork(watchLoadCurrentFieldset),
    fork(watchCreateFieldset),
    fork(watchUpdateFieldset),
    fork(watchDeleteFieldset),
  ]);
}

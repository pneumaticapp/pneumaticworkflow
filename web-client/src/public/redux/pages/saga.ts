import { all, fork, takeEvery, put } from 'redux-saga/effects';

import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';

import { EPagesActions, loadPagesFailed, loadPagesSuccess } from './actions';

import { IPages } from '../../types/page';
import { getPages } from '../../api/getPages';

function* loadPagesSaga() {
  try {
    const pages: IPages = yield getPages();
    yield put(loadPagesSuccess(pages));
  } catch (error) {
    yield put(loadPagesFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load pages', error);
  }
}

export function* watchLoadPages() {
  yield takeEvery(EPagesActions.LoadPages, loadPagesSaga);
}

export function* rootSaga() {
  yield all([fork(watchLoadPages)]);
}

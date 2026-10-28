import type { CallEffect } from 'redux-saga/effects';
import type { Task } from 'redux-saga';
import { cancel, fork, put } from 'redux-saga/effects';

import { waitForAction } from '../../utils/waitForAction';
import { closeCreatePerformerModal, createPerformerFailed, createPerformerStarted } from '../slice';

export function* submitCreatePerformer(request: CallEffect) {
  yield put(createPerformerStarted());
  const modalCloseWatcher: Task = yield fork(waitForAction, closeCreatePerformerModal.type);

  try {
    yield request;
    if (modalCloseWatcher.isRunning()) {
      yield put(closeCreatePerformerModal());
    }
  } catch (error) {
    if (modalCloseWatcher.isRunning()) {
      yield put(createPerformerFailed());
    }
    throw error;
  } finally {
    yield cancel(modalCloseWatcher);
  }
}

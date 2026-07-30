import { all, fork, takeEvery, put } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { generateMenu } from '../menu/actions';
import { getAiAgents } from '../../api/aiAgents/getAiAgents';
import { createAiAgent as createAiAgentApi } from '../../api/aiAgents/createAiAgent';
import { updateAiAgent as updateAiAgentApi } from '../../api/aiAgents/updateAiAgent';
import { deleteAiAgent as deleteAiAgentApi } from '../../api/aiAgents/deleteAiAgent';
import { getAiConnection, IGetAiConnectionResponse } from '../../api/aiAgents/getAiConnection';
import { setAiConnection, ISetAiConnectionResponse } from '../../api/aiAgents/setAiConnection';
import { deleteAiConnection } from '../../api/aiAgents/deleteAiConnection';
import { IAiAgent, TAiAgentDraft, TAiConnectionDraft } from './types';

import {
  loadAiAgents,
  createAiAgent,
  updateAiAgent,
  deleteAiAgent,
  loadAiAgentsSuccess,
  loadAiAgentsFailed,
  createAiAgentSuccess,
  updateAiAgentSuccess,
  deleteAiAgentSuccess,
  aiAgentRequestFailed,
  loadAiConnection,
  saveAiConnection,
  removeAiConnection,
  loadAiConnectionSuccess,
  loadAiConnectionFailed,
  saveAiConnectionSuccess,
  removeAiConnectionSuccess,
  aiConnectionRequestFailed,
} from './slice';

function* loadAiAgentsSaga() {
  try {
    const agents: IAiAgent[] = yield getAiAgents();

    yield put(loadAiAgentsSuccess(agents));
  } catch (error) {
    // 403 means AI performers are not enabled for the account
    yield put(loadAiAgentsFailed());
    if (error?.status !== 403) {
      logger.error('failed to load AI agents', error);
    }
  } finally {
    // the AI Agents menu item visibility depends on the fetch result
    yield put(generateMenu());
  }
}

function* createAiAgentSaga(action: PayloadAction<TAiAgentDraft>) {
  try {
    const agent: IAiAgent = yield createAiAgentApi(action.payload);

    yield put(createAiAgentSuccess(agent));
  } catch (error) {
    yield put(aiAgentRequestFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI agent', error);
  }
}

function* updateAiAgentSaga(action: PayloadAction<IAiAgent>) {
  try {
    const { id, ...draft } = action.payload;
    const agent: IAiAgent = yield updateAiAgentApi(id, draft);

    yield put(updateAiAgentSuccess(agent));
  } catch (error) {
    yield put(aiAgentRequestFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update AI agent', error);
  }
}

function* deleteAiAgentSaga(action: PayloadAction<Pick<IAiAgent, 'id'>>) {
  try {
    yield deleteAiAgentApi(action.payload.id);

    yield put(deleteAiAgentSuccess(action.payload));
  } catch (error) {
    yield put(aiAgentRequestFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI agent', error);
  }
}

function* loadAiConnectionSaga() {
  try {
    const response: IGetAiConnectionResponse = yield getAiConnection();

    yield put(loadAiConnectionSuccess(response.connection));
  } catch (error) {
    // 403 means the deployment has no AI performers or the user
    // cannot manage the connection
    yield put(loadAiConnectionFailed());
    if (error?.status !== 403) {
      logger.error('failed to load AI provider connection', error);
    }
  } finally {
    // the AI Agents menu item is also shown to admins who can
    // connect a provider but have not done it yet
    yield put(generateMenu());
  }
}

function* saveAiConnectionSaga(action: PayloadAction<TAiConnectionDraft>) {
  try {
    const response: ISetAiConnectionResponse = yield setAiConnection(action.payload);

    yield put(saveAiConnectionSuccess(response.connection));
    // a saved key switches the feature on for the account
    yield put(loadAiAgents());
  } catch (error) {
    yield put(aiConnectionRequestFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to save AI provider connection', error);
  }
}

function* removeAiConnectionSaga() {
  try {
    yield deleteAiConnection();

    yield put(removeAiConnectionSuccess());
    // without a key the feature may switch off for the account
    yield put(loadAiAgents());
  } catch (error) {
    yield put(aiConnectionRequestFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to remove AI provider connection', error);
  }
}

export function* watchLoadAiAgents() {
  yield takeEvery(loadAiAgents.type, loadAiAgentsSaga);
}

export function* watchCreateAiAgent() {
  yield takeEvery(createAiAgent.type, createAiAgentSaga);
}

export function* watchUpdateAiAgent() {
  yield takeEvery(updateAiAgent.type, updateAiAgentSaga);
}

export function* watchDeleteAiAgent() {
  yield takeEvery(deleteAiAgent.type, deleteAiAgentSaga);
}

export function* watchLoadAiConnection() {
  yield takeEvery(loadAiConnection.type, loadAiConnectionSaga);
}

export function* watchSaveAiConnection() {
  yield takeEvery(saveAiConnection.type, saveAiConnectionSaga);
}

export function* watchRemoveAiConnection() {
  yield takeEvery(removeAiConnection.type, removeAiConnectionSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadAiAgents),
    fork(watchCreateAiAgent),
    fork(watchUpdateAiAgent),
    fork(watchDeleteAiAgent),
    fork(watchLoadAiConnection),
    fork(watchSaveAiConnection),
    fork(watchRemoveAiConnection),
  ]);
}

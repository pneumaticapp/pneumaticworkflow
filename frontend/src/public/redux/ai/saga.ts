import { all, fork, put, takeEvery, takeLatest } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';

import {
  createAIAgent as createAIAgentApi,
  createAIProvider as createAIProviderApi,
  deleteAIAgent as deleteAIAgentApi,
  deleteAIProvider as deleteAIProviderApi,
  getAIAgents as getAIAgentsApi,
  getAIProviderModels as getAIProviderModelsApi,
  getAIProviders as getAIProvidersApi,
  updateAIAgent as updateAIAgentApi,
} from '../../api/ai';
import { IAIAgent, IAIModel, IAIProvider, ICreateAIAgentRequest, ICreateAIProviderRequest } from '../../types/ai';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';

import {
  createAIAgent,
  createAIProvider,
  deleteAIAgent,
  deleteAIProvider,
  loadAIAgents,
  loadAIAgentsFailed,
  loadAIAgentsStarted,
  loadAIAgentsSuccess,
  loadAIProviderModels,
  loadAIProviderModelsFailed,
  loadAIProviderModelsStarted,
  loadAIProviderModelsSuccess,
  loadAIProviders,
  loadAIProvidersFailed,
  loadAIProvidersStarted,
  loadAIProvidersSuccess,
  savingFinished,
  savingStarted,
  updateAIAgent,
} from './slice';

function* fetchAIProviders() {
  yield put(loadAIProvidersStarted());

  try {
    const providers: IAIProvider[] = yield getAIProvidersApi();
    yield put(loadAIProvidersSuccess(providers));
  } catch (error) {
    yield put(loadAIProvidersFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load AI providers', error);
  }
}

function* fetchAIAgents() {
  yield put(loadAIAgentsStarted());

  try {
    const agents: IAIAgent[] = yield getAIAgentsApi();
    yield put(loadAIAgentsSuccess(agents));
  } catch (error) {
    yield put(loadAIAgentsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load AI agents', error);
  }
}

function* fetchAIProviderModels({ payload: providerId }: PayloadAction<number>) {
  yield put(loadAIProviderModelsStarted(providerId));

  try {
    const models: IAIModel[] = yield getAIProviderModelsApi(providerId);
    yield put(loadAIProviderModelsSuccess({ providerId, models }));
  } catch (error) {
    yield put(loadAIProviderModelsFailed(providerId));
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load AI provider models', error);
  }
}

function* createAIProviderSaga({ payload }: PayloadAction<ICreateAIProviderRequest>) {
  yield put(savingStarted());

  try {
    yield createAIProviderApi(payload);
    yield fetchAIProviders();
    NotificationManager.success({ message: 'ai-providers.created' });
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI provider', error);
  } finally {
    yield put(savingFinished());
  }
}

function* deleteAIProviderSaga({ payload: id }: PayloadAction<number>) {
  yield put(savingStarted());

  try {
    yield deleteAIProviderApi(id);
    yield fetchAIProviders();
    NotificationManager.success({ message: 'ai-providers.deleted' });
  } catch (error) {
    // The API refuses to delete a provider still referenced by an agent (MSG_AI_0005).
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI provider', error);
  } finally {
    yield put(savingFinished());
  }
}

function* createAIAgentSaga({ payload }: PayloadAction<ICreateAIAgentRequest>) {
  yield put(savingStarted());

  try {
    yield createAIAgentApi(payload);
    // Providers carry a usage list, which the new agent has just changed.
    yield all([fetchAIAgents(), fetchAIProviders()]);
    NotificationManager.success({ message: 'team.ai-agents.created' });
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI agent', error);
  } finally {
    yield put(savingFinished());
  }
}

function* updateAIAgentSaga({
  payload: { id, ...data },
}: PayloadAction<{ id: number } & Partial<ICreateAIAgentRequest>>) {
  yield put(savingStarted());

  try {
    yield updateAIAgentApi(id, data);
    yield all([fetchAIAgents(), fetchAIProviders()]);
    NotificationManager.success({ message: 'team.ai-agents.updated' });
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update AI agent', error);
  } finally {
    yield put(savingFinished());
  }
}

function* deleteAIAgentSaga({ payload: id }: PayloadAction<number>) {
  yield put(savingStarted());

  try {
    yield deleteAIAgentApi(id);
    yield all([fetchAIAgents(), fetchAIProviders()]);
    NotificationManager.success({ message: 'team.ai-agents.deleted' });
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI agent', error);
  } finally {
    yield put(savingFinished());
  }
}

export function* watchAIProviders() {
  yield takeEvery(loadAIProviders, fetchAIProviders);
  yield takeEvery(createAIProvider, createAIProviderSaga);
  yield takeEvery(deleteAIProvider, deleteAIProviderSaga);
  // takeLatest: switching providers in the agent form must drop the previous models request.
  yield takeLatest(loadAIProviderModels, fetchAIProviderModels);
}

export function* watchAIAgents() {
  yield takeEvery(loadAIAgents, fetchAIAgents);
  yield takeEvery(createAIAgent, createAIAgentSaga);
  yield takeEvery(updateAIAgent, updateAIAgentSaga);
  yield takeEvery(deleteAIAgent, deleteAIAgentSaga);
}

export function* rootSaga() {
  yield all([fork(watchAIProviders), fork(watchAIAgents)]);
}

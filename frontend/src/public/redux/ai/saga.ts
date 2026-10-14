import { all, fork, put, takeEvery, takeLatest } from 'redux-saga/effects';
import type { PayloadAction } from '@reduxjs/toolkit';

import {
  createAIAgent as createAIAgentApi,
  createAIProvider as createAIProviderApi,
  createAIProviderByVendor as createAIProviderByVendorApi,
  deleteAIAgent as deleteAIAgentApi,
  deleteAIProvider as deleteAIProviderApi,
  getAIAgents as getAIAgentsApi,
  getAIProviderModels as getAIProviderModelsApi,
  getAIProviders as getAIProvidersApi,
  getAIVendors as getAIVendorsApi,
  updateAIAgent as updateAIAgentApi,
} from '../../api/ai';
import type { IAIAgent, IAIModel, IAIProvider, ICreateAIAgentRequest, IAIVendor } from '../../types/ai';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';

import {
  createAIAgent,
  createAIAgentFailed,
  createAIAgentStarted,
  createAIAgentSucceeded,
  createAIProvider,
  createAIProviderByVendor,
  createAIProviderFailed,
  createAIProviderStarted,
  createAIProviderSucceeded,
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
  loadAIVendors,
  loadAIVendorsFailed,
  loadAIVendorsStarted,
  loadAIVendorsSuccess,
  savingFinished,
  savingStarted,
  updateAIAgent,
} from './slice';

let latestProvidersRequestId = 0;

function* fetchAIProviders() {
  const requestId = ++latestProvidersRequestId;
  yield put(loadAIProvidersStarted());

  try {
    const providers: IAIProvider[] = yield getAIProvidersApi();
    if (requestId !== latestProvidersRequestId) {
      return false;
    }
    yield put(loadAIProvidersSuccess(providers));
    return true;
  } catch (error) {
    if (requestId === latestProvidersRequestId) {
      yield put(loadAIProvidersFailed());
      NotificationManager.warning({ message: getErrorMessage(error) });
    }
    logger.error('failed to load AI providers', error);
    return false;
  }
}

function* fetchAIVendors() {
  yield put(loadAIVendorsStarted());

  try {
    const vendors: IAIVendor[] = yield getAIVendorsApi();
    yield put(loadAIVendorsSuccess(vendors));
    return true;
  } catch (error) {
    yield put(loadAIVendorsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load AI vendors', error);
    return false;
  }
}

let latestAgentsRequestId = 0;

function* fetchAIAgents() {
  const requestId = ++latestAgentsRequestId;
  yield put(loadAIAgentsStarted());

  try {
    const agents: IAIAgent[] = yield getAIAgentsApi();
    if (requestId !== latestAgentsRequestId) {
      return false;
    }
    yield put(loadAIAgentsSuccess(agents));
    return true;
  } catch (error) {
    if (requestId === latestAgentsRequestId) {
      yield put(loadAIAgentsFailed());
      NotificationManager.warning({ message: getErrorMessage(error) });
    }
    logger.error('failed to load AI agents', error);
    return false;
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

export function* createAIProviderSaga({ payload, meta }: ReturnType<typeof createAIProvider>) {
  yield put(savingStarted());
  yield put(createAIProviderStarted(meta.requestId));

  try {
    yield createAIProviderApi(payload);
    yield put(createAIProviderSucceeded(meta.requestId));
    const isRefreshed: boolean = yield fetchAIProviders();
    if (isRefreshed) {
      NotificationManager.success({ message: 'ai-providers.created' });
    }
  } catch (error) {
    yield put(createAIProviderFailed(meta.requestId));
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI provider', error);
  } finally {
    yield put(savingFinished());
  }
}

export function* createAIProviderByVendorSaga({ payload, meta }: ReturnType<typeof createAIProviderByVendor>) {
  yield put(savingStarted());
  yield put(createAIProviderStarted(meta.requestId));

  try {
    yield createAIProviderByVendorApi(payload);
    yield put(createAIProviderSucceeded(meta.requestId));
    const isRefreshed: boolean = yield fetchAIProviders();
    if (isRefreshed) {
      NotificationManager.success({ message: 'ai-providers.created' });
    }
  } catch (error) {
    yield put(createAIProviderFailed(meta.requestId));
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI provider by vendor', error);
  } finally {
    yield put(savingFinished());
  }
}

function* deleteAIProviderSaga({ payload: id }: PayloadAction<number>) {
  yield put(savingStarted());

  try {
    yield deleteAIProviderApi(id);
    const isRefreshed: boolean = yield fetchAIProviders();
    if (isRefreshed) {
      NotificationManager.success({ message: 'ai-providers.deleted' });
    }
  } catch (error) {
    // The API refuses to delete a provider still referenced by an agent (MSG_AI_0005).
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI provider', error);
  } finally {
    yield put(savingFinished());
  }
}

export function* createAIAgentSaga({ payload, meta }: ReturnType<typeof createAIAgent>) {
  yield put(savingStarted());
  yield put(createAIAgentStarted(meta.requestId));

  try {
    yield createAIAgentApi(payload);
    yield put(createAIAgentSucceeded(meta.requestId));
    // Providers carry a usage list, which the new agent has just changed.
    const [areAgentsRefreshed, areProvidersRefreshed]: [boolean, boolean] = yield all([
      fetchAIAgents(),
      fetchAIProviders(),
    ]);
    if (areAgentsRefreshed && areProvidersRefreshed) {
      NotificationManager.success({ message: 'team.ai-agents.created' });
    }
  } catch (error) {
    yield put(createAIAgentFailed(meta.requestId));
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
    const [areAgentsRefreshed, areProvidersRefreshed]: [boolean, boolean] = yield all([
      fetchAIAgents(),
      fetchAIProviders(),
    ]);
    if (areAgentsRefreshed && areProvidersRefreshed) {
      NotificationManager.success({ message: 'team.ai-agents.updated' });
    }
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
    const [areAgentsRefreshed, areProvidersRefreshed]: [boolean, boolean] = yield all([
      fetchAIAgents(),
      fetchAIProviders(),
    ]);
    if (areAgentsRefreshed && areProvidersRefreshed) {
      NotificationManager.success({ message: 'team.ai-agents.deleted' });
    }
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI agent', error);
  } finally {
    yield put(savingFinished());
  }
}

export function* watchAIProviders() {
  yield takeEvery(loadAIVendors, fetchAIVendors);
  yield takeEvery(loadAIProviders, fetchAIProviders);
  yield takeEvery(createAIProvider, createAIProviderSaga);
  yield takeEvery(createAIProviderByVendor, createAIProviderByVendorSaga);
  yield takeEvery(deleteAIProvider, deleteAIProviderSaga);
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

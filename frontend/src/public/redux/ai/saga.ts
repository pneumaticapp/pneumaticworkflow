import { all, call, cancel, fork, put, take, takeEvery, takeLatest } from 'redux-saga/effects';
import type { Task } from 'redux-saga';
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
import type {
  IAIAgent,
  IAIModel,
  IAIProvider,
  IAIVendor,
  ICreateAIAgentRequest,
  ICreateAIProviderByVendorRequest,
  ICreateAIProviderRequest,
} from '../../api/ai/types';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { uploadUserAvatar } from '../../utils/uploadFiles';
import type { TUploadedFile } from '../../utils/uploadFiles';
import { closeCreateUserModal } from '../accounts/slice';

import {
  createAIAgent,
  createAIAgentFailed,
  createAIAgentStarted,
  createAIAgentSuccess,
  createAIProvider,
  createAIProviderByVendor,
  createAIProviderFailed,
  createAIProviderStarted,
  createAIProviderSuccess,
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
  updateAIAgent,
  uploadAIAgentAvatar,
  cancelAIAgentAvatarUpload,
  closeCreateAIProviderModal,
  uploadAIAgentAvatarStarted,
  uploadAIAgentAvatarFinished,
} from './slice';
import type { TUpdateAIAgentPayload } from './types';

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

function* waitForAction(actionType: string) {
  yield take(actionType);
}

function* createProvider(createRequest: () => Promise<unknown>) {
  yield put(createAIProviderStarted());
  const modalCloseWatcher: Task = yield fork(waitForAction, closeCreateAIProviderModal.type);

  try {
    yield call(createRequest);
    if (modalCloseWatcher.isRunning()) {
      yield put(createAIProviderSuccess());
    }
    const isRefreshed: boolean = yield fetchAIProviders();
    if (isRefreshed) {
      NotificationManager.success({ message: 'ai-providers.created' });
    }
  } catch (error) {
    if (modalCloseWatcher.isRunning()) {
      yield put(createAIProviderFailed());
    }
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI provider', error);
  } finally {
    yield cancel(modalCloseWatcher);
  }
}

export function* createAIProviderSaga({ payload }: PayloadAction<ICreateAIProviderRequest>) {
  yield createProvider(() => createAIProviderApi(payload));
}

export function* createAIProviderByVendorSaga({ payload }: PayloadAction<ICreateAIProviderByVendorRequest>) {
  yield createProvider(() => createAIProviderByVendorApi(payload));
}

function* deleteAIProviderSaga({ payload: id }: PayloadAction<number>) {
  try {
    yield deleteAIProviderApi(id);
    const isRefreshed: boolean = yield fetchAIProviders();
    if (isRefreshed) {
      NotificationManager.success({ message: 'ai-providers.deleted' });
    }
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI provider', error);
  }
}

function* refreshAgentsAndProviders(successMessage: string) {
  const [isAgentsRefreshed, isProvidersRefreshed]: [boolean, boolean] = yield all([
    fetchAIAgents(),
    fetchAIProviders(),
  ]);
  if (isAgentsRefreshed && isProvidersRefreshed) {
    NotificationManager.success({ message: successMessage });
  }
}

export function* createAIAgentSaga({ payload }: PayloadAction<ICreateAIAgentRequest>) {
  yield put(createAIAgentStarted());
  const modalCloseWatcher: Task = yield fork(waitForAction, closeCreateUserModal.type);

  try {
    yield call(createAIAgentApi, payload);
    if (modalCloseWatcher.isRunning()) {
      yield cancel(modalCloseWatcher);
      yield put(createAIAgentSuccess());
      yield put(closeCreateUserModal());
    }
    yield refreshAgentsAndProviders('team.ai-agents.created');
  } catch (error) {
    if (modalCloseWatcher.isRunning()) {
      yield put(createAIAgentFailed());
    }
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create AI agent', error);
  } finally {
    yield cancel(modalCloseWatcher);
  }
}

export function* updateAIAgentSaga({
  payload: { id, onSuccess, onError, ...data },
}: PayloadAction<TUpdateAIAgentPayload>) {
  try {
    yield updateAIAgentApi(id, data);
    onSuccess?.();
    yield refreshAgentsAndProviders('team.ai-agents.updated');
  } catch (error) {
    onError?.();
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to update AI agent', error);
  }
}

function* deleteAIAgentSaga({ payload: id }: PayloadAction<number>) {
  try {
    yield deleteAIAgentApi(id);
    yield refreshAgentsAndProviders('team.ai-agents.deleted');
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete AI agent', error);
  }
}

export function* uploadAIAgentAvatarSaga(
  action: ReturnType<typeof uploadAIAgentAvatar> | ReturnType<typeof cancelAIAgentAvatarUpload>,
) {
  if (!uploadAIAgentAvatar.match(action)) return;

  const { file, onSuccess } = action.payload;
  yield put(uploadAIAgentAvatarStarted());

  try {
    const [uploaded]: TUploadedFile[] = yield call(uploadUserAvatar, file);
    if (uploaded?.url && !uploaded.error) {
      onSuccess(uploaded.url);
    }
  } catch (error) {
    NotificationManager.warning({ message: 'file-service.upload-failed' });
    logger.error('failed to upload AI agent avatar', error);
  } finally {
    yield put(uploadAIAgentAvatarFinished());
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
  yield takeLatest([uploadAIAgentAvatar, cancelAIAgentAvatarUpload], uploadAIAgentAvatarSaga);
}

export function* rootSaga() {
  yield all([fork(watchAIProviders), fork(watchAIAgents)]);
}

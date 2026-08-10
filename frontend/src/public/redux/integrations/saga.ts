import { all, fork, takeEvery, call, put, takeLatest, takeLeading } from 'redux-saga/effects';
import { getApiKeys, createApiKey as createApiKeyApi, deleteApiKey as deleteApiKeyApi } from '../../api/getApiKey';
import { getIntegrationDetails } from '../../api/getIntegrationDetails';
import { getIntegrations } from '../../api/getIntegrations';
import { NotificationManager } from '../../components/UI/Notifications';
import { ERoutes } from '../../constants/routes';
import { IApiKeyItem, IIntegrationDetailed, IIntegrationListItem, IApiKeyCreateResponse } from '../../types/integrations';
import { history } from '../../utils/history';
import { logger } from '../../utils/logger';
import {
  EIntegrationsActions,
  loadIntegrationsListSuccess,
  loadIntegrationDetailsFailed,
  loadIntegrationsListFailed,
  loadIntegrationDetailsSuccess,
  TLoadIntegrationDetails,
  loadApiKeysSuccess,
  loadApiKeysFailed,
  TCreateApiKey,
  createApiKeySuccess,
  createApiKeyFailed,
  TDeleteApiKey,
  deleteApiKeySuccess,
  deleteApiKeyFailed,
} from './actions';

function* fetchIntegrationsList() {
  try {
    const integrationsList: IIntegrationListItem[] = yield call(getIntegrations);
    yield put(loadIntegrationsListSuccess(integrationsList));
  } catch (error) {
    yield put(loadIntegrationsListFailed());
    logger.info('fetch integrations list error : ', error);
    NotificationManager.warning({ message: 'integrations.list-fetch-failed' });
  }
}

function* fetchIntegrationDetails({ payload: { id } }: TLoadIntegrationDetails) {
  if (!Number.isInteger(id)) {
    history.replace(ERoutes.Integrations);
    NotificationManager.warning({ message: 'integrations.not-found' });

    return;
  }

  try {
    const integrationDetails: IIntegrationDetailed = yield call(getIntegrationDetails, id);
    yield put(loadIntegrationDetailsSuccess(integrationDetails));
  } catch (error) {
    yield put(loadIntegrationDetailsFailed());
    logger.info('fetch integration details error : ', error);

    const isIntegrationNotFound = error && error.detail === 'Not found.';
    const message = isIntegrationNotFound ? 'integrations.not-found' : 'integrations.details-fetch-failed';
    NotificationManager.warning({ message });

    history.replace(ERoutes.Integrations);
  }
}

export function* fetchApiKeys() {
  try {
    const apiKeys: IApiKeyItem[] = yield call(getApiKeys);
    yield put(loadApiKeysSuccess(apiKeys));
  } catch (error) {
    yield put(loadApiKeysFailed());
    NotificationManager.notifyApiError(error, { message: 'integrations.fetch-api-key-error' });
    logger.error(error);
  }
}

export function* handleCreateApiKey({ payload }: TCreateApiKey) {
  try {
    const response: IApiKeyCreateResponse = yield call(createApiKeyApi, payload.name || '');
    const { token: rawKey, ...apiKeyData } = response;
    yield put(createApiKeySuccess({ apiKey: apiKeyData as IApiKeyItem, rawKey }));
  } catch (error) {
    yield put(createApiKeyFailed());
    NotificationManager.notifyApiError(error, { message: 'integrations.create-api-key-error' });
    logger.error(error);
  }
}

export function* handleDeleteApiKey({ payload }: TDeleteApiKey) {
  try {
    yield call(deleteApiKeyApi, payload.id);
    yield put(deleteApiKeySuccess({ id: payload.id }));
    NotificationManager.success({ message: 'integrations.api-key-revoked' });
  } catch (error) {
    yield put(deleteApiKeyFailed());
    NotificationManager.notifyApiError(error, { message: 'integrations.delete-api-key-error' });
    logger.error(error);
  }
}

export function* watchLoadIntegrationsList() {
  yield takeEvery(EIntegrationsActions.LoadIntegrationsList, fetchIntegrationsList);
}

export function* watchLoadIntegrationDetails() {
  yield takeEvery(EIntegrationsActions.LoadIntegrationDetails, fetchIntegrationDetails);
}

export function* watchFetchApiKeys() {
  yield takeLatest(EIntegrationsActions.LoadApiKeys, fetchApiKeys);
}

export function* watchCreateApiKey() {
  yield takeLeading(EIntegrationsActions.CreateApiKey, handleCreateApiKey);
}

export function* watchDeleteApiKey() {
  yield takeEvery(EIntegrationsActions.DeleteApiKey, handleDeleteApiKey);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchApiKeys),
    fork(watchCreateApiKey),
    fork(watchDeleteApiKey),
    fork(watchLoadIntegrationsList),
    fork(watchLoadIntegrationDetails),
  ]);
}

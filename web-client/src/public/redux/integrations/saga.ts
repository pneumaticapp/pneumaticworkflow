/* eslint-disable */
/* prettier-ignore */
import { all, fork, takeEvery, call, put, takeLatest, select } from 'redux-saga/effects';
import { getApiKey } from '../../api/getApiKey';
import { getIntegrationDetails } from '../../api/getIntegrationDetails';
import { getIntegrations } from '../../api/getIntegrations';
import { NotificationManager } from '../../components/UI/Notifications';
import { ERoutes } from '../../constants/routes';
import { IIntegrationDetailed, IIntegrationListItem } from '../../types/integrations';
import { history } from '../../utils/history';
import { logger } from '../../utils/logger';
import { getUserApiKey } from '../selectors/user';
import {
  EIntegrationsActions,
  loadIntegrationsListSuccess,
  loadIntegrationDetailsFailed,
  loadIntegrationsListFailed,
  loadIntegrationDetailsSuccess,
  TLoadIntegrationDetails,
  loadApiKeySuccess,
  loadApiKeyFailed,
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

export function* fetchApiKey() {
  try {
    const { data: currentApiKey }: ReturnType<typeof getUserApiKey> = yield select(getUserApiKey);
    if (currentApiKey) {
      yield put(loadApiKeySuccess(currentApiKey));

      return;
    }

    const { token } = yield getApiKey();
    yield put(loadApiKeySuccess(token));
  } catch (e) {
    yield put(loadApiKeyFailed());
    NotificationManager.error({ message: 'integrations.fetch-api-key-error' });
    logger.error(e);
  }
}

export function* watchLoadIntegrationsList() {
  yield takeEvery(EIntegrationsActions.LoadIntegrationsList, fetchIntegrationsList);
}

export function* watchLoadIntegrationDetails() {
  yield takeEvery(EIntegrationsActions.LoadIntegrationDetails, fetchIntegrationDetails);
}

export function* watchFetchApiKey() {
  yield takeLatest(EIntegrationsActions.LoadApiKey, fetchApiKey);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchApiKey),
    fork(watchLoadIntegrationsList),
    fork(watchLoadIntegrationDetails),
  ]);
}

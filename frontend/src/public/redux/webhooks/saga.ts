/* eslint-disable */
/* prettier-ignore */
import { all, call, put, fork, takeEvery, select } from 'redux-saga/effects';
import { EWebhooksActions, setWebhooksUrl, setWebhooksStatus, TAddWebhook, TRemoveWebhook } from '../actions';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { unsubscribeFromWebhooks } from '../../api/unsubscribeFromWebhooks';
import { subscribeToWebhooks } from '../../api/subscribeToWebhooks';
import { EWebhooksSubscriberStatus, EWebhooksTypeEvent } from '../../types/webhooks';
import { loadWebhooks, TLoadWebhooksResponse } from '../../api/loadWebhooks';
import { getWebhooks } from '../selectors/webhooks';
import { IWebhookStore } from '../../types/redux';

function* updateWebhooksStatus(status: EWebhooksSubscriberStatus) {
  const webhooks: IWebhookStore = yield select(getWebhooks);

  // tslint:disable-next-line: forin
  for (const event in webhooks) {
    yield put(setWebhooksStatus({
      event: event as EWebhooksTypeEvent,
      status,
    }));
  }
}

function* loadWebhooksSaga() {
  try {
    yield updateWebhooksStatus(EWebhooksSubscriberStatus.Loading);

    const webhooksResponse: TLoadWebhooksResponse[] = yield call(loadWebhooks);

    for (const event of webhooksResponse) {
      yield put(setWebhooksUrl({
        event: event.event,
        url: event.url,
      }));

      const status = event.url ?
        EWebhooksSubscriberStatus.Subscribed :
        EWebhooksSubscriberStatus.NotSubscribed;

      yield put(setWebhooksStatus({
        event: event.event,
        status,
      }));
    }

  } catch (error) {
    logger.info('add webooks subscriber error: ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
    yield updateWebhooksStatus(EWebhooksSubscriberStatus.Unknown);
  }
}

function* addWebhooksSaga({ payload }: TAddWebhook) {
  const webhooks: IWebhookStore = yield select(getWebhooks);
  const prevStatus: EWebhooksSubscriberStatus = webhooks[payload.event].status;

  try {
    yield put(setWebhooksStatus({
      event: payload.event,
      status: EWebhooksSubscriberStatus.Subscribing,
    }));

    if (payload.url !== null) {
      yield call(subscribeToWebhooks, payload.event, payload.url);

      yield put(setWebhooksUrl({
        event: payload.event,
        url: payload.url,
      }));

      yield put(setWebhooksStatus({
        event: payload.event,
        status: EWebhooksSubscriberStatus.Subscribed,
      }));

      NotificationManager.success({ message: 'template.intergrations-webhook-subscribe-success' });
    }
  } catch (error) {
    logger.info('add webooks subscriber error: ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
    yield put(setWebhooksStatus({
      event: payload.event,
      status: prevStatus,
    }));
  }
}

function* removeWebhooksSaga({ payload: { event } }: TRemoveWebhook) {
  const webhooks: IWebhookStore = yield select(getWebhooks);
  const prevStatus: EWebhooksSubscriberStatus = webhooks[event].status;

  try {
    yield put(setWebhooksStatus({
      event,
      status: EWebhooksSubscriberStatus.Unsubscribing,
    }));

    yield call(unsubscribeFromWebhooks, event);

    yield put(setWebhooksUrl({
      event,
      url: null,
    }));

    yield put(setWebhooksStatus({
      event,
      status: EWebhooksSubscriberStatus.NotSubscribed,
    }));

    NotificationManager.success({ message: 'template.intergrations-webhook-unsubscribe-success' });

  } catch (error) {
    logger.info('remove webooks subscriber error: ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
    yield put(setWebhooksStatus({
      event,
      status: prevStatus,
    }));
  }
}

export function* watchLoadWebhooks() {
  yield takeEvery(EWebhooksActions.LoadWebhooks, loadWebhooksSaga);
}

export function* watchAddWebhooks() {
  yield takeEvery(EWebhooksActions.AddWebhooks, addWebhooksSaga);
}

export function* watchRemoveWebhooks() {
  yield takeEvery(EWebhooksActions.RemoveWebhooks, removeWebhooksSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadWebhooks),
    fork(watchAddWebhooks),
    fork(watchRemoveWebhooks),
  ]);
}

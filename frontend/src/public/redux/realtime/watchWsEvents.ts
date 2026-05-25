import { call, put, select, take } from 'redux-saga/effects';

import { updateTaskWorkflowLogItem } from '../actions';
import { changeNotificationsList, changeUnreadNotificationsCount } from '../notifications/actions';
import { getNotificationsStore } from '../selectors/notifications';
import { getTaskStore } from '../selectors/task';
import { getUserTimezone } from '../selectors/user';
import { getWorkflowsStore } from '../selectors/workflows';
import { handleAddTask, handleRemoveTask } from '../tasks/saga';
import { createWebSocketChannel } from '../utils/createWebSocketChannel';
import { updateWorkflowLogItem } from '../workflows/slice';
import { parseCookies } from '../../utils/cookie';
import { envWssURL } from '../../constants/enviroment';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapBackendNewEventToRedux } from '../../utils/mappers';
import { mergePaths } from '../../utils/urls';
import type { IStoreTask, IStoreWorkflows } from '../../types/redux';
import type { TNotificationsListItem } from '../../types';

import { mapRealtimeEnvelopeToNotificationItem } from './utils/mapNotificationFromWs';
import { mapTaskCreatedDataToListItem } from './utils/mapTaskCreatedToListItem';
import { mapWsEnvelopeToWorkflowLogItem } from './utils/mapWorkflowLogEventFromWs';
import type { IRealtimeWsEnvelope, INotificationWsEnvelope } from './types';
import { isNotificationWsEventType } from './types';

function* prependNotificationItem(item: TNotificationsListItem): Generator {
  const {
    items: currentNotificationsList,
    totalItemsCount,
    unreadItemsCount,
    isNotificationsListOpen,
  }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);
  const nextItems = [item, ...currentNotificationsList];
  yield put(changeNotificationsList({ items: nextItems, count: totalItemsCount + 1 }));

  if (!isNotificationsListOpen) {
    yield put(changeUnreadNotificationsCount(unreadItemsCount + 1));
  }
}

function* routeRealtimeEvent(envelope: IRealtimeWsEnvelope): Generator {
  switch (envelope.type) {
    case 'task_created': {
      const task = mapTaskCreatedDataToListItem(envelope.data);
      yield* handleAddTask(task);
      break;
    }
    case 'task_completed':
    case 'task_deleted': {
      yield* handleRemoveTask(envelope.data.id);
      break;
    }
    case 'event_created':
    case 'event_updated': {
      const logItem = mapWsEnvelopeToWorkflowLogItem(envelope);

      if (!logItem) {
        break;
      }

      const timezone: ReturnType<typeof getUserTimezone> = yield select(getUserTimezone);
      const { data }: IStoreTask = yield select(getTaskStore);
      const { workflow }: IStoreWorkflows = yield select(getWorkflowsStore);
      const formatted = mapBackendNewEventToRedux(logItem, timezone);

      if (logItem.workflowId === data?.workflow.id || logItem.workflowId === workflow?.id) {
        yield put(updateWorkflowLogItem(formatted));
        yield put(updateTaskWorkflowLogItem(formatted));
      }

      break;
    }
    default:
      if (isNotificationWsEventType(envelope.type)) {
        const item = mapRealtimeEnvelopeToNotificationItem(envelope as INotificationWsEnvelope);
        if (item) {
          yield* prependNotificationItem(item);
        }
      }
  }
}

export function* watchWsEvents(): Generator {
  const { api: { wsPublicUrl, urls } } = getBrowserConfigEnv();
  const url = mergePaths(
    envWssURL || wsPublicUrl,
    `${urls.wsEvents}?auth_token=${parseCookies(document.cookie).token}`,
  );

  const channel = yield call(createWebSocketChannel, url);

  while (true) {
    const envelope = (yield take(channel)) as IRealtimeWsEnvelope;
    yield* routeRealtimeEvent(envelope);
  }
}

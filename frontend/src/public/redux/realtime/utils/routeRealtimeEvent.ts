import { call, put, select } from 'redux-saga/effects';

import type { IRealtimeWsEnvelope } from '../types';
import type { IStoreTask, IStoreWorkflows } from '../../../types/redux';
import { ERealtimeEnvelopeType } from '../types';

import { handleAddTask, handleRemoveTask } from '../../tasks/saga';
import { upsertUserFromWs, removeUserFromWs } from '../../accounts/slice';
import { mapWsUserToListItem } from './mapUserFromWs';
import { mapTaskCreatedDataToListItem } from './mapTaskCreatedToListItem';
import { upsertGroupFromWs, removeGroupFromWs, updateTaskWorkflowLogItem } from '../../actions';
import { mapWsGroupToGroup } from './mapGroupFromWs';
import { mapWsEnvelopeToWorkflowLogItem } from './mapWorkflowLogEventFromWs';
import { mapNotificationCreatedDataToListItem } from './mapNotificationFromWs';
import { prependNotificationItem } from './prependNotificationItem';
import { logger } from '../../../utils/logger';
import { getUserTimezone } from '../../selectors/user';
import { updateWorkflowLogItem } from '../../workflows/slice';
import { isWorkflowEndedEventType } from './isWorkflowEndedEventType';
import { mapBackendNewEventToRedux } from '../../../utils/mappers';
import { getWorkflowsStore } from '../../selectors/workflows';
import { getTaskStore } from '../../selectors/task';
import { getTasksSettings } from '../../selectors/tasks';
import {
  shouldDecrementCounterOnDeleted,
  shouldRemoveTaskOnDeleted,
} from './shouldRemoveTaskOnDeleted';

export function* routeRealtimeEvent(envelope: IRealtimeWsEnvelope) {
  switch (envelope.type) {
    case ERealtimeEnvelopeType.TASK_CREATED: {
      const task = mapTaskCreatedDataToListItem(envelope.data);
      yield call(handleAddTask, task);
      break;
    }
    case ERealtimeEnvelopeType.TASK_COMPLETED: {
      yield call(handleRemoveTask, envelope.data.id, true);
      break;
    }
    case ERealtimeEnvelopeType.TASK_DELETED: {
      const settings: ReturnType<typeof getTasksSettings> = yield select(getTasksSettings);
      const { status } = envelope.data;

      if (
        !shouldRemoveTaskOnDeleted({
          status,
          completionStatus: settings.completionStatus,
        })
      ) {
        break;
      }

      yield call(
        handleRemoveTask,
        envelope.data.id,
        shouldDecrementCounterOnDeleted(status),
      );
      break;
    }
    case ERealtimeEnvelopeType.USER_CREATED:
    case ERealtimeEnvelopeType.USER_UPDATED: {
      yield put(upsertUserFromWs(mapWsUserToListItem(envelope.data)));
      break;
    }
    case ERealtimeEnvelopeType.USER_DELETED: {
      yield put(removeUserFromWs(envelope.data.id));
      break;
    }
    case ERealtimeEnvelopeType.GROUP_CREATED:
    case ERealtimeEnvelopeType.GROUP_UPDATED: {
      yield put(upsertGroupFromWs(mapWsGroupToGroup(envelope.data)));
      break;
    }
    case ERealtimeEnvelopeType.GROUP_DELETED: {
      yield put(removeGroupFromWs(envelope.data.id));
      break;
    }
    case ERealtimeEnvelopeType.EVENT_CREATED:
    case ERealtimeEnvelopeType.EVENT_UPDATED: {
      const logItem = mapWsEnvelopeToWorkflowLogItem(envelope);

      if (!logItem) {
        logger.error(`unhandled WebSocket event: ${envelope.type}, id=${envelope.id}`);
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

      if (
        envelope.type === ERealtimeEnvelopeType.EVENT_CREATED &&
        logItem.task?.id &&
        isWorkflowEndedEventType(logItem.type)
      ) {
        yield call(handleRemoveTask, logItem.task.id);
      }

      break;
    }
    case ERealtimeEnvelopeType.NOTIFICATION_CREATED: {
      const item = mapNotificationCreatedDataToListItem(envelope.data);

      if (item) {
        yield call(prependNotificationItem, item);
      } else {
        logger.error(`unhandled WebSocket event: ${envelope.type}`);
      }

      break;
    }
    default: {
      const unexpectedEnvelope = envelope as IRealtimeWsEnvelope;
      logger.error(`unhandled WebSocket event: ${String(unexpectedEnvelope.type)}`);
      break;
    }
  }
}

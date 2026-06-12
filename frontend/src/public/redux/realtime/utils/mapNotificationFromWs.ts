import type { TNotificationsListItem } from '../../../types';
import { toISOStringFromTsp } from '../../../utils/dateTime';

import type { IWsNotificationCreatedData } from '../types';
import { isNotificationDataType } from '../types';

export type TNotificationMappingEnvelope = {
  [Type in IWsNotificationCreatedData['type']]: {
    type: Type;
    data: Extract<IWsNotificationCreatedData, { type: Type }>;
  };
}[IWsNotificationCreatedData['type']];

function mapNotificationEnvelopeToListItem(
  envelope: TNotificationMappingEnvelope,
): TNotificationsListItem | null {
  switch (envelope.type) {
    case 'comment':
    case 'mention':
    case 'reaction': {
      const { data } = envelope;
      if (data.author === null || !data.task || !data.workflow || data.text === null) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: envelope.type,
        author: data.author,
        text: data.text,
        workflow: data.workflow,
        task: data.task,
      };
    }
    case 'system': {
      const { data } = envelope;
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'system',
        text: data.text ?? '',
      };
    }
    case 'urgent':
    case 'not_urgent': {
      const { data } = envelope;
      if (data.author === null || !data.task || !data.workflow) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: envelope.type,
        author: data.author,
        text: '',
        workflow: data.workflow,
        task: data.task,
      };
    }
    case 'overdue_task': {
      const { data } = envelope;
      if (!data.task || !data.workflow) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'overdue_task',
        workflow: data.workflow,
        task: data.task,
      };
    }
    case 'snooze_workflow': {
      const { data } = envelope;
      if (data.author === null || !data.task?.delay || !data.workflow) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'snooze_workflow',
        author: data.author,
        workflow: data.workflow,
        task: {
          id: data.task.id,
          name: data.task.name,
          delay: {
            estimatedEndDate: toISOStringFromTsp(data.task.delay.estimatedEndDateTsp),
            duration: data.task.delay.duration,
          },
        },
      };
    }
    case 'resume_workflow': {
      const { data } = envelope;
      if (data.author === null || !data.task || !data.workflow) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'resume_workflow',
        author: data.author,
        workflow: data.workflow,
        task: data.task,
      };
    }
    case 'due_date_changed': {
      const { data } = envelope;
      const { dueDateTsp } = data.task ?? {};
      if (!data.task || !data.workflow || data.author === null) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'due_date_changed',
        author: data.author,
        text: null,
        workflow: data.workflow,
        task: {
          id: data.task.id,
          name: data.task.name,
          dueDate: typeof dueDateTsp === 'number' ? toISOStringFromTsp(dueDateTsp) : null,
        },
      };
    }
    case 'complete_task': {
      const { data } = envelope;
      if (!data.task || !data.workflow || data.author === null) {
        return null;
      }
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'complete_task',
        author: data.author,
        text: null,
        workflow: data.workflow,
        task: data.task,
      };
    }
    default:
      return null;
  }
}

export function mapNotificationCreatedDataToListItem(
  data: IWsNotificationCreatedData,
): TNotificationsListItem | null {
  if (!isNotificationDataType(data.type)) {
    return null;
  }

  return mapNotificationEnvelopeToListItem({
    type: data.type,
    data,
  } as TNotificationMappingEnvelope);
}

/** @deprecated Use mapNotificationCreatedDataToListItem for notification_created payloads */
export function mapRealtimeEnvelopeToNotificationItem(
  envelope: TNotificationMappingEnvelope,
): TNotificationsListItem | null {
  return mapNotificationEnvelopeToListItem(envelope);
}

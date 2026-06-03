import type { TNotificationsListItem } from '../../../types';
import { toISOStringFromTsp } from '../../../utils/dateTime';

import type { INotificationWsEnvelope } from '../wsPayloads';

export function mapRealtimeEnvelopeToNotificationItem(envelope: INotificationWsEnvelope): TNotificationsListItem | null {
  switch (envelope.type) {
    case 'comment':
    case 'mention':
    case 'reaction': {
      const { data } = envelope;
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
        text: data.text,
      };
    }
    case 'urgent':
    case 'not_urgent': {
      const { data } = envelope;
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
      return {
        id: data.id,
        status: data.status,
        datetime: toISOStringFromTsp(data.datetimeTsp),
        type: 'overdue_task',
        workflow: data.workflow,
        task: data.task,
      };
    }
    case 'delay_workflow': {
      const { data } = envelope;
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
      const {dueDateTsp} = data.task;
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
    default:
      return null;
  }
}

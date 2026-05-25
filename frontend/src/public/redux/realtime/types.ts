import type {
  IRealtimeWsEnvelope,
  INotificationWsEnvelope,
  TNotificationWsEventType,
} from './wsPayloads';

export type {
  IRealtimeWsEnvelope,
  INotificationWsEnvelope,
  TNotificationWsEventType,
};
export type {
  IWsTaskCreatedData,
  IWsTaskCompletedData,
  IWsTaskDeletedData,
} from './wsPayloads';

export type TRealtimeEventType =
  | 'task_created'
  | 'task_completed'
  | 'task_deleted'
  | TNotificationWsEventType
  | 'event_created'
  | 'event_updated'
  | 'user_created'
  | 'user_updated'
  | 'user_deleted'
  | 'group_created'
  | 'group_updated'
  | 'group_deleted';

export const REALTIME_EVENT_TYPES: readonly TRealtimeEventType[] = [
  'task_created',
  'task_completed',
  'task_deleted',
  'delay_workflow',
  'resume_workflow',
  'due_date_changed',
  'urgent',
  'not_urgent',
  'system',
  'comment',
  'mention',
  'reaction',
  'event_created',
  'event_updated',
  'user_created',
  'user_updated',
  'user_deleted',
  'group_created',
  'group_updated',
  'group_deleted',
  'overdue_task',
] as const;

export const NOTIFICATION_WS_TYPES: ReadonlySet<TNotificationWsEventType> = new Set([
  'comment',
  'mention',
  'reaction',
  'system',
  'urgent',
  'not_urgent',
  'overdue_task',
  'delay_workflow',
  'resume_workflow',
  'due_date_changed',
]);

export function isNotificationWsEventType(type: string): type is TNotificationWsEventType {
  return NOTIFICATION_WS_TYPES.has(type as TNotificationWsEventType);
}

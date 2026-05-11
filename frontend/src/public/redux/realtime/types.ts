/**
 * WebSocket `/ws/events` envelope (see Public API Websockets spec).
 * Wire format uses snake_case; normalize with mapToCamelCase where frames are read.
 */
export type TRealtimeEventType =
  | 'task_created'
  | 'task_completed'
  | 'task_deleted'
  | 'delay_workflow'
  | 'resume_workflow'
  | 'due_date_changed'
  | 'urgent'
  | 'not_urgent'
  | 'system'
  | 'comment'
  | 'mention'
  | 'reaction'
  | 'event_created'
  | 'event_updated'
  | 'user_created'
  | 'user_updated'
  | 'user_deleted'
  | 'group_created'
  | 'group_updated'
  | 'group_deleted'
  | 'overdue_task';

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

export interface IRealtimeWsEnvelope {
  id: string;
  dateCreatedTsp: number;
  type: string;
  data: unknown;
}

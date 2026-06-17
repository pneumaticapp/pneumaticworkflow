import { IWorkflowLogItem } from "../../types/workflow";
import { EUserGroupType } from "../team/types";

export interface IWsEnvelopeBase {
  id: string;
  dateCreatedTsp: number;
}

export enum ERealtimeEnvelopeType {
  TASK_COMPLETED = 'task_completed',
  TASK_CREATED = 'task_created',
  TASK_DELETED = 'task_deleted',
  EVENT_CREATED = 'event_created',
  EVENT_UPDATED = 'event_updated',
  NOTIFICATION_CREATED = 'notification_created',
  USER_CREATED = 'user_created',
  USER_UPDATED = 'user_updated',
  USER_DELETED = 'user_deleted',
  GROUP_CREATED = 'group_created',
  GROUP_UPDATED = 'group_updated',
  GROUP_DELETED = 'group_deleted',
}

export type IRealtimeWsEnvelope =
  // task events
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.TASK_CREATED; data: IWsTaskCreatedData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.TASK_COMPLETED; data: IWsTaskCompletedData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.TASK_DELETED; data: IWsTaskDeletedData })
  // user events
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.USER_CREATED; data: IWsUserData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.USER_UPDATED; data: IWsUserData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.USER_DELETED; data: IWsUserData })
  // group events
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.GROUP_CREATED; data: IWsGroupData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.GROUP_UPDATED; data: IWsGroupData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.GROUP_DELETED; data: IWsGroupData })
  // notification events
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.NOTIFICATION_CREATED; data: IWsNotificationCreatedData })
  // process events
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.EVENT_CREATED; data: IWsEventCreatedData })
  | (IWsEnvelopeBase & { type: ERealtimeEnvelopeType.EVENT_UPDATED; data: IWsEventUpdatedData })



// ======================= event

export interface IWsTaskCompletedData {
  id: number;
  name: string;
  workflowName: string;
  dateCompletedTsp: number;
  performers: IWsTaskPerformer[];
}

export interface IWsTaskCreatedData {
  id: number;
  name: string;
  workflowName: string;
  dateStartedTsp: number;
  dueDateTsp: number | null;
  templateId: number;
  templateTaskApiName: string;
  isUrgent: boolean;
}

export interface IWsTaskDeletedData {
  id: number;
  name: string;
  workflowName: string;
}

export interface IWsDelayWorkflowData {
  id: number;
  author: number;
  type: 'snooze_workflow';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef & {
    delay: IWsNotificationDelay;
  };
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsResumeWorkflowData {
  id: number;
  author: number;
  type: 'resume_workflow';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsDueDateChangedData {
  id: number;
  author: number;
  type: 'due_date_changed';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef & {
    dueDateTsp: number | null;
  };
  workflow: IWsNotificationWorkflowRef;
}


export interface IWsUrgentData {
  id: number;
  author: number;
  type: 'urgent';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsNotUrgentData {
  id: number;
  author: number;
  type: 'not_urgent';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsSystemData {
  id: number;
  author: number | null;
  type: 'system';
  datetimeTsp: number;
  status: 'new' | 'read';
  text: string;
}

export interface IWsCommentData {
  id: number;
  author: number;
  text: string;
  type: 'comment';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsMentionData {
  id: number;
  author: number;
  text: string;
  type: 'mention';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsReactionData {
  id: number;
  author: number;
  text: string;
  type: 'reaction';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsOverdueTaskData {
  id: number;
  author: number | null;
  type: 'overdue_task';
  datetimeTsp: number;
  status: 'new' | 'read';
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export interface IWsCompleteTaskData {
  id: number;
  author: number;
  type: 'complete_task';
  datetimeTsp: number;
  status: 'new' | 'read';
  text: string | null;
  task: IWsNotificationTaskRef;
  workflow: IWsNotificationWorkflowRef;
}

export type IWsNotificationCreatedData =
  | IWsCommentData
  | IWsMentionData
  | IWsReactionData
  | IWsSystemData
  | IWsUrgentData
  | IWsNotUrgentData
  | IWsOverdueTaskData
  | IWsDelayWorkflowData
  | IWsResumeWorkflowData
  | IWsDueDateChangedData
  | IWsCompleteTaskData;

export type IWsEventCreatedData = IWorkflowLogItem;

export type IWsEventUpdatedData = IWorkflowLogItem;

export interface IWsUserData {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  photo: string | null;
  isAdmin: boolean;
  isAccountOwner: boolean;
  managerId: number | null;
  subordinatesIds: number[];
}

export interface IWsGroupData {
  id: number;
  name: string;
  photo: string | null;
  type: EUserGroupType;
  users: IWsGroupUser[];
}

// ======================= utils

export interface IWsNotificationTaskRef {
  id: number;
  name: string;
}
  
export interface IWsNotificationDelay {
  estimatedEndDateTsp: number;
  duration: string;
}
  
export interface IWsNotificationWorkflowRef {
  id: number;
  name: string;
}

export interface IWsTaskPerformer {
  sourceId: number;
  type: 'user' | 'group';
  isCompleted: boolean;
  dateCompletedTsp: number | null;
}

export interface IWsGroupUser extends IWsUserData {}


// ======================= notification data types

export type TNotificationDataType =
  | 'overdue_task'
  | 'complete_task'
  | 'system'
  | 'urgent'
  | 'not_urgent'
  | 'comment'
  | 'mention'
  | 'reaction'
  | 'snooze_workflow'
  | 'resume_workflow'
  | 'due_date_changed';

export const NOTIFICATION_DATA_TYPES: readonly TNotificationDataType[] = [
  'overdue_task',
  'complete_task',
  'system',
  'urgent',
  'not_urgent',
  'comment',
  'mention',
  'reaction',
  'snooze_workflow',
  'resume_workflow',
  'due_date_changed',
] as const;

export function isNotificationDataType(type: string): type is TNotificationDataType {
  return (NOTIFICATION_DATA_TYPES as readonly string[]).includes(type);
}

export type TNotificationWsEventType = TNotificationDataType;

export const NOTIFICATION_WS_TYPES: ReadonlySet<TNotificationWsEventType> = new Set(
  NOTIFICATION_DATA_TYPES,
);

export function isNotificationWsEventType(type: string): type is TNotificationWsEventType {
  return NOTIFICATION_WS_TYPES.has(type as TNotificationWsEventType);
}

export type INotificationWsEnvelope = {
  type: TNotificationWsEventType;
  data: IWsNotificationCreatedData;
};

export type TRealtimeEventType = ERealtimeEnvelopeType;

export const REALTIME_EVENT_TYPES: readonly ERealtimeEnvelopeType[] = Object.values(
  ERealtimeEnvelopeType,
);
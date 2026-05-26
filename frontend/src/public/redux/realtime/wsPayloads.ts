export interface IWsEnvelopeBase {
  id: string;
  dateCreatedTsp: number;
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

export interface IWsTaskPerformer {
  sourceId: number;
  type: 'user' | 'group';
  isCompleted: boolean;
  dateCompletedTsp: number | null;
}

export interface IWsTaskCompletedData {
  id: number;
  name: string;
  workflowName: string;
  dateCompletedTsp: number;
  performers: IWsTaskPerformer[];
}

export interface IWsNotificationTaskRef {
  id: number;
  name: string;
}

export interface IWsNotificationWorkflowRef {
  id: number;
  name: string;
}

export interface IWsNotificationDelay {
  estimatedEndDateTsp: number;
  duration: string;
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

export interface IWsEventCreatedTask {
  id: number;
  name: string;
  number: number;
  description: string;
  dueDateTsp: number;
  performers: IWsTaskPerformer[];
}

export interface IWsEventCreatedData {
  id: number;
  createdTsp: number;
  type: number;
  workflowId: number;
  task: IWsEventCreatedTask;
}

export interface IWsEventUpdatedWatched {
  dateTsp: number;
  userId: number;
}

export interface IWsEventUpdatedAttachment {
  id: number;
  name: string;
  url: string;
  thumbnailUrl: string;
  size: number;
}

export interface IWsEventUpdatedTask {
  id: number;
  name: string;
  number: number;
}

export interface IWsEventUpdatedData {
  id: number;
  createdTsp: number;
  updatedTsp: number;
  status: 'created' | 'updated' | 'deleted';
  type: number;
  workflowId: number;
  text: string | null;
  reactions: Record<string, number[]>;
  watched: IWsEventUpdatedWatched[];
  task: IWsEventUpdatedTask;
  attachments: IWsEventUpdatedAttachment[];
}

export interface IWsUserData {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  photo: string | null;
  isAdmin: boolean;
  isAccountOwner: boolean;
}

export interface IWsGroupUser extends IWsUserData {}

export interface IWsGroupData {
  id: number;
  name: string;
  photo: string | null;
  users: IWsGroupUser[];
}

export type TNotificationWsEventType =
  | 'comment'
  | 'mention'
  | 'reaction'
  | 'system'
  | 'urgent'
  | 'not_urgent'
  | 'overdue_task'
  | 'delay_workflow'
  | 'resume_workflow'
  | 'due_date_changed';

export type IRealtimeWsEnvelope =
  | (IWsEnvelopeBase & { type: 'task_created'; data: IWsTaskCreatedData })
  | (IWsEnvelopeBase & { type: 'task_completed'; data: IWsTaskCompletedData })
  | (IWsEnvelopeBase & { type: 'task_deleted'; data: IWsTaskDeletedData })
  | (IWsEnvelopeBase & { type: 'delay_workflow'; data: IWsDelayWorkflowData })
  | (IWsEnvelopeBase & { type: 'resume_workflow'; data: IWsResumeWorkflowData })
  | (IWsEnvelopeBase & { type: 'due_date_changed'; data: IWsDueDateChangedData })
  | (IWsEnvelopeBase & { type: 'urgent'; data: IWsUrgentData })
  | (IWsEnvelopeBase & { type: 'not_urgent'; data: IWsNotUrgentData })
  | (IWsEnvelopeBase & { type: 'system'; data: IWsSystemData })
  | (IWsEnvelopeBase & { type: 'comment'; data: IWsCommentData })
  | (IWsEnvelopeBase & { type: 'mention'; data: IWsMentionData })
  | (IWsEnvelopeBase & { type: 'reaction'; data: IWsReactionData })
  | (IWsEnvelopeBase & { type: 'event_created'; data: IWsEventCreatedData })
  | (IWsEnvelopeBase & { type: 'event_updated'; data: IWsEventUpdatedData })
  | (IWsEnvelopeBase & { type: 'user_created'; data: IWsUserData })
  | (IWsEnvelopeBase & { type: 'user_updated'; data: IWsUserData })
  | (IWsEnvelopeBase & { type: 'user_deleted'; data: IWsUserData })
  | (IWsEnvelopeBase & { type: 'group_created'; data: IWsGroupData })
  | (IWsEnvelopeBase & { type: 'group_updated'; data: IWsGroupData })
  | (IWsEnvelopeBase & { type: 'group_deleted'; data: IWsGroupData })
  | (IWsEnvelopeBase & { type: 'overdue_task'; data: IWsOverdueTaskData });

export type INotificationWsEnvelope = Extract<
  IRealtimeWsEnvelope,
  { type: TNotificationWsEventType }
>;

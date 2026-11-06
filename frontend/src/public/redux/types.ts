import type { EWorkflowsLogSorting, IWorkflowLogItem } from '../types/workflow';

export interface IAction<Type> {
  type: Type;
}

export interface ITypedReduxAction<Type, Payload> extends IAction<Type> {
  payload: Payload;
}

export interface IChangeWorkflowLogViewSettingsPayload {
  id: number;
  sorting: EWorkflowsLogSorting;
  comments: boolean;
  isOnlyAttachmentsShown: boolean;
}

export interface ISendWorkflowLogComment {
  text: string;
  taskId?: number;
}

export interface IWorkflowLog {
  items: IWorkflowLogItem[];
  isCommentsShown: boolean;
  isOnlyAttachmentsShown: boolean;
  isSkippedTasksShown: boolean;
  sorting: EWorkflowsLogSorting;
  isOpen: boolean;
  workflowId: number | null;
  isLoading: boolean;
}

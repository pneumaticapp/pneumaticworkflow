import { ITypedReduxAction, IWorkflowLog } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { IExtraField, RawPerformer } from '../../types/template';
import { ITask } from '../../types/tasks';
import { ETaskCardViewMode } from '../../components/TaskCard';
import { EWorkflowsLogSorting, IWorkflowDetailsClient, IWorkflowLogItem } from '../../types/workflow';
import { ISendWorkflowLogComment } from '../workflows/types';

export const enum ETaskActions {
  LoadCurrentTask = 'LOAD_CURRENT_TASK',
  SetCurrentTask = 'SET_CURRENT_TASK',
  ChangeTaskWorkflowLog = 'CHANGE_TASK_WORKFLOW_LOG',
  ChangeTaskWorkflow = 'CHANGE_TASK_WORKFLOW',
  SetTaskWorkflowIsLoading = 'SET_TASK_WORKFLOW_IS_LOADING',
  ChangeTaskWorkflowLogViewSettings = 'CHANGE_TASK_WORKFLOW_LOG_VIEW_SETTINGS',
  SendTaskWorkflowLogComment = 'SEND_TASK_WORKFLOW_LOG_COMMENT',
  UpdateTaskWorkflowLogItem = 'UPDATE_TASK_WORKFLOW_LOG_ITEM',
  PatchCurrentTask = 'PATCH_CURRENT_TASK',
  SetTaskCompleted = 'SET_TASK_COMPLETED',
  SetTaskReverted = 'SET_TASK_REVERTED',
  SetCurrentTaskStatus = 'SET_CURRENT_TASK_STATUS',
  AddTaskPerformer = 'ADD_TASK_PERFORMER',
  RemoveTaskPerformer = 'REMOVE_TASK_PERFORMER',
  ChangeTaskPerformers = 'CHANGE_TASK_PERFORMERS',
  AddTaskGuest = 'ADD_TASK_GUEST',
  ChangeChecklistItem = 'CHANGE_CHECKLIST_ITEM',
  MarkChecklistItem = 'MARK_CHECKLIST_ITEM',
  UnmarkChecklistItem = 'UNMARK_CHECKLIST_ITEM',
  SetChecklistsHandling = 'SET_CHECKLISTS_HANDLING',
  SetCurrentTaskDueDate = 'SET_CURRENT_TASK_DUE_DATE',
  DeleteCurrentTaskDueDate = 'DELETE_CURRENT_TASK_DUE_DATE',
}

export type TLoadCurrentTaskPayload = {
  taskId: number;
  viewMode?: ETaskCardViewMode;
};
export type TLoadCurrentTask = ITypedReduxAction<ETaskActions.LoadCurrentTask, TLoadCurrentTaskPayload>;
export const loadCurrentTask: (payload: TLoadCurrentTaskPayload) => TLoadCurrentTask = actionGenerator<
  ETaskActions.LoadCurrentTask,
  TLoadCurrentTaskPayload
>(ETaskActions.LoadCurrentTask);

export type TSetCurrentTask = ITypedReduxAction<ETaskActions.SetCurrentTask, ITask | null>;
export const setCurrentTask: (payload: ITask | null) => TSetCurrentTask = actionGenerator<
  ETaskActions.SetCurrentTask,
  ITask | null
>(ETaskActions.SetCurrentTask);

export type TChangeTaskWorkflow = ITypedReduxAction<ETaskActions.ChangeTaskWorkflow, IWorkflowDetailsClient>;
export const changeTaskWorkflow: (payload: IWorkflowDetailsClient) => TChangeTaskWorkflow = actionGenerator<
  ETaskActions.ChangeTaskWorkflow,
  IWorkflowDetailsClient
>(ETaskActions.ChangeTaskWorkflow);

export type TChangeTaskWorkflowLog = ITypedReduxAction<ETaskActions.ChangeTaskWorkflowLog, Partial<IWorkflowLog>>;
export const changeTaskWorkflowLog: (payload: Partial<IWorkflowLog>) => TChangeTaskWorkflowLog = actionGenerator<
  ETaskActions.ChangeTaskWorkflowLog,
  Partial<IWorkflowLog>
>(ETaskActions.ChangeTaskWorkflowLog);

export type TSetTaskWorkflowIsLoading = ITypedReduxAction<ETaskActions.SetTaskWorkflowIsLoading, boolean>;
export const setTaskWorkflowIsLoading: (payload: boolean) => TSetTaskWorkflowIsLoading = actionGenerator<
  ETaskActions.SetTaskWorkflowIsLoading,
  boolean
>(ETaskActions.SetTaskWorkflowIsLoading);
export interface IChangeTaskWorkflowLogViewSettingsPayload {
  taskId: number;
  id: number;
  sorting: EWorkflowsLogSorting;
  comments: boolean;
  isOnlyAttachmentsShown: boolean;
}
export type TChangeTaskWorkflowLogViewSettings = ITypedReduxAction<
  ETaskActions.ChangeTaskWorkflowLogViewSettings,
  IChangeTaskWorkflowLogViewSettingsPayload
>;
export const changeTaskWorkflowLogViewSettings: (
  payload: IChangeTaskWorkflowLogViewSettingsPayload,
) => TChangeTaskWorkflowLogViewSettings = actionGenerator<
  ETaskActions.ChangeTaskWorkflowLogViewSettings,
  IChangeTaskWorkflowLogViewSettingsPayload
>(ETaskActions.ChangeTaskWorkflowLogViewSettings);

export type TPatchCurrentTask = ITypedReduxAction<ETaskActions.PatchCurrentTask, Partial<ITask>>;
export const patchCurrentTask: (payload: Partial<ITask>) => TPatchCurrentTask = actionGenerator<
  ETaskActions.PatchCurrentTask,
  Partial<ITask>
>(ETaskActions.PatchCurrentTask);

export type TSetCurrentTaskDueDate = ITypedReduxAction<ETaskActions.SetCurrentTaskDueDate, string>;
export const setCurrentTaskDueDate: (payload: string) => TSetCurrentTaskDueDate = actionGenerator<
  ETaskActions.SetCurrentTaskDueDate,
  string
>(ETaskActions.SetCurrentTaskDueDate);

export type TDeleteCurrentTaskDueDate = ITypedReduxAction<ETaskActions.DeleteCurrentTaskDueDate, void>;
export const deleteCurrentTaskDueDate: (payload?: void) => TDeleteCurrentTaskDueDate = actionGenerator<
  ETaskActions.DeleteCurrentTaskDueDate,
  void
>(ETaskActions.DeleteCurrentTaskDueDate);

export type TSetTaskCompletedPayload = {
  taskId: number;
  output: IExtraField[];
  viewMode: ETaskCardViewMode;
};
export type TSetTaskCompleted = ITypedReduxAction<ETaskActions.SetTaskCompleted, TSetTaskCompletedPayload>;
export const setTaskCompleted: (payload: TSetTaskCompletedPayload) => TSetTaskCompleted = actionGenerator<
  ETaskActions.SetTaskCompleted,
  TSetTaskCompletedPayload
>(ETaskActions.SetTaskCompleted);

export type TSetTaskRevertedPayload = {
  taskId: number;
  viewMode: ETaskCardViewMode;
  comment: string;
};
export type TSetTaskReverted = ITypedReduxAction<ETaskActions.SetTaskReverted, TSetTaskRevertedPayload>;
export const setTaskReverted: (payload: TSetTaskRevertedPayload) => TSetTaskReverted = actionGenerator<
  ETaskActions.SetTaskReverted,
  TSetTaskRevertedPayload
>(ETaskActions.SetTaskReverted);

export enum ETaskStatus {
  WaitingForAction = 'waiting-for-action',
  Loading = 'loading',
  Returning = 'returning',
  Completing = 'completing',
  Completed = 'completed',
}
export type TSetCurrentTaskStatus = ITypedReduxAction<ETaskActions.SetCurrentTaskStatus, ETaskStatus>;
export const setCurrentTaskStatus: (payload: ETaskStatus) => TSetCurrentTaskStatus = actionGenerator<
  ETaskActions.SetCurrentTaskStatus,
  ETaskStatus
>(ETaskActions.SetCurrentTaskStatus);

export type TAddTaskPerformerPayload = { taskId: number; userId: RawPerformer };
export type TAddTaskPerformer = ITypedReduxAction<ETaskActions.AddTaskPerformer, TAddTaskPerformerPayload>;
export const addTaskPerformer: (payload: TAddTaskPerformerPayload) => TAddTaskPerformer = actionGenerator<
  ETaskActions.AddTaskPerformer,
  TAddTaskPerformerPayload
>(ETaskActions.AddTaskPerformer);

export type TRemoveTaskPerformerPayload = { taskId: number; userId: RawPerformer };
export type TRemoveTaskPerformer = ITypedReduxAction<ETaskActions.RemoveTaskPerformer, TRemoveTaskPerformerPayload>;
export const removeTaskPerformer: (payload: TRemoveTaskPerformerPayload) => TRemoveTaskPerformer = actionGenerator<
  ETaskActions.RemoveTaskPerformer,
  TRemoveTaskPerformerPayload
>(ETaskActions.RemoveTaskPerformer);

type TChangeTaskPerformersPayload = RawPerformer[];
export type TChangeTaskPerformers = ITypedReduxAction<ETaskActions.ChangeTaskPerformers, TChangeTaskPerformersPayload>;
export const changeTaskPerformers: (payload: TChangeTaskPerformersPayload) => TChangeTaskPerformers = actionGenerator<
  ETaskActions.ChangeTaskPerformers,
  TChangeTaskPerformersPayload
>(ETaskActions.ChangeTaskPerformers);

export type TAddTaskGuestPayload = {
  taskId: number;
  guestEmail: string;
  onStartUploading?(): void;
  onEndUploading?(): void;
  onError?(): void;
};
export type TAddTaskGuest = ITypedReduxAction<ETaskActions.AddTaskGuest, TAddTaskGuestPayload>;
export const addTaskGuest: (payload: TAddTaskGuestPayload) => TAddTaskGuest = actionGenerator<
  ETaskActions.AddTaskGuest,
  TAddTaskGuestPayload
>(ETaskActions.AddTaskGuest);

type TChangeChecklistItemPayload = {
  listApiName: string;
  itemApiName: string;
  isChecked: boolean;
};
export type TChangeChecklistItem = ITypedReduxAction<ETaskActions.ChangeChecklistItem, TChangeChecklistItemPayload>;
export const changeChecklistItem: (payload: TChangeChecklistItemPayload) => TChangeChecklistItem = actionGenerator<
  ETaskActions.ChangeChecklistItem,
  TChangeChecklistItemPayload
>(ETaskActions.ChangeChecklistItem);

export type TMarkChecklistItemPayload = {
  listApiName: string;
  itemApiName: string;
};
export type TMarkChecklistItem = ITypedReduxAction<ETaskActions.MarkChecklistItem, TMarkChecklistItemPayload>;
export const markChecklistItem: (payload: TMarkChecklistItemPayload) => TMarkChecklistItem = actionGenerator<
  ETaskActions.MarkChecklistItem,
  TMarkChecklistItemPayload
>(ETaskActions.MarkChecklistItem);

export type TUnmarkChecklistItemPayload = {
  listApiName: string;
  itemApiName: string;
};
export type TUnmarkChecklistItem = ITypedReduxAction<ETaskActions.UnmarkChecklistItem, TUnmarkChecklistItemPayload>;
export const unmarkChecklistItem: (payload: TUnmarkChecklistItemPayload) => TUnmarkChecklistItem = actionGenerator<
  ETaskActions.UnmarkChecklistItem,
  TUnmarkChecklistItemPayload
>(ETaskActions.UnmarkChecklistItem);

export type TSetChecklistsHandling = ITypedReduxAction<ETaskActions.SetChecklistsHandling, boolean>;
export const setChecklistsHandling: (payload: boolean) => TSetChecklistsHandling = actionGenerator<
  ETaskActions.SetChecklistsHandling,
  boolean
>(ETaskActions.SetChecklistsHandling);

export type TSendTaskWorkflowLogComment = ITypedReduxAction<
  ETaskActions.SendTaskWorkflowLogComment,
  ISendWorkflowLogComment
>;

export const sendTaskWorkflowLogComments: (payload: ISendWorkflowLogComment) => TSendTaskWorkflowLogComment =
  actionGenerator<ETaskActions.SendTaskWorkflowLogComment, ISendWorkflowLogComment>(
    ETaskActions.SendTaskWorkflowLogComment,
  );

export type TUpdateTaskWorkflowLogItemPayload = IWorkflowLogItem;
export type TUpdateTaskWorkflowLogItem = ITypedReduxAction<
  ETaskActions.UpdateTaskWorkflowLogItem,
  TUpdateTaskWorkflowLogItemPayload
>;
export const updateTaskWorkflowLogItem: (payload: TUpdateTaskWorkflowLogItemPayload) => TUpdateTaskWorkflowLogItem =
  actionGenerator<ETaskActions.UpdateTaskWorkflowLogItem, TUpdateTaskWorkflowLogItemPayload>(
    ETaskActions.UpdateTaskWorkflowLogItem,
  );

export type TTaskActions =
  | TLoadCurrentTask
  | TChangeTaskWorkflow
  | TChangeTaskWorkflowLog
  | TSetTaskWorkflowIsLoading
  | TChangeTaskWorkflowLogViewSettings
  | TSetCurrentTask
  | TPatchCurrentTask
  | TSetCurrentTaskDueDate
  | TDeleteCurrentTaskDueDate
  | TSetTaskCompleted
  | TSetTaskReverted
  | TSetCurrentTaskStatus
  | TAddTaskPerformer
  | TRemoveTaskPerformer
  | TChangeTaskPerformers
  | TAddTaskGuest
  | TChangeChecklistItem
  | TUpdateTaskWorkflowLogItem
  | TMarkChecklistItem
  | TSendTaskWorkflowLogComment
  | TUnmarkChecklistItem
  | TSetChecklistsHandling;

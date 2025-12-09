import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { IWorkflowClient } from '../../types/workflow';
import { IKickoff, TOrderedFields } from '../../types/template';
import { TUploadedFile } from '../../utils/uploadFiles';
import { IDeleteComment } from '../../api/workflows/deleteComment';
import { IEditComment } from '../../api/workflows/editComment';

export const enum EWorkflowsActions {
  ResetWorkflowsList = 'RESET_WORKFLOWS_LIST',
  EditWorkflow = 'EDIT_WORKFLOW',
  EditWorkflowFail = 'EDIT_WORKFLOW_FAIL',
  DeleteWorkflow = 'DELETE_WORKFLOW',
  ReturnWorkflowToTask = 'RETURN_WORKFLOW_TO_TASK',
  CloneWorkflow = 'CLONE_WORKFLOW',
  ToggleIsUrgent = 'TOGGLE_IS_URGENT',
  UpdateWorkflowStartersCounters = 'UPDATE_WORKFLOW_STARTERS_COUNTERS',
  SnoozeWorkflow = 'SNOOZE_WORKFLOW',

  UpdateCurrentPerformersCounters = 'UPDATE_CURRENT_PERFORMERS_COUNTERS',

  UpdateWorkflowsTemplateStepsCounters = 'UPDATE_WORKFLOW_TEMPLATE_STEPS_COUNTERS',

  SetLoadingWorkflowLogComments = 'SET_LOADING_WORKFLOW_LOG_COMMENTS',
  SendWorkflowLogComment = 'SEND_WORKFLOW_LOG_COMMENT',
  DeleteComment = 'DELETE_COMMENT',
  EditComment = 'EDIT_COMMENT',

  SaveWorkflowsPreset = 'SAVE_WORKFLOWS_PRESET',
}

export interface IStartWorkflowPayload {
  id: number;
  name: string;
  kickoff: {
    [key: string]: string;
  } | null;
  ancestorTaskId?: number;
  isUrgent?: boolean;
  dueDateTsp?: number | null;
}

export type TEditWorkflowPayload = {
  typeChange?: string;
  name?: string;
  kickoff?: IKickoff | null;
  isUrgent?: boolean;
  dueDate?: string | null;
  workflowId: number;
  dueDateTsp?: number | null;
};
export type TEditWorkflow = ITypedReduxAction<EWorkflowsActions.EditWorkflow, TEditWorkflowPayload>;
export const editWorkflow: (payload: TEditWorkflowPayload) => TEditWorkflow = actionGenerator<
  EWorkflowsActions.EditWorkflow,
  TEditWorkflowPayload
>(EWorkflowsActions.EditWorkflow);

export type TSetWorkflowResumedPayload = {
  workflowId: number;
  onSuccess?(): void;
};

export type TSetWorkflowFinishedPayload = {
  workflowId: number;
  onWorkflowEnded?(): void;
};

export interface ISendWorkflowLogComment {
  text: string;
  attachments: TUploadedFile[];
  taskId?: number;
}

export type TSendWorkflowLogComment = ITypedReduxAction<
  EWorkflowsActions.SendWorkflowLogComment,
  ISendWorkflowLogComment
>;

export const sendWorkflowLogComments: (payload: ISendWorkflowLogComment) => TSendWorkflowLogComment = actionGenerator<
  EWorkflowsActions.SendWorkflowLogComment,
  ISendWorkflowLogComment
>(EWorkflowsActions.SendWorkflowLogComment);

type TDeleteWorkflowPayload = {
  workflowId: number;
  onSuccess?(): void;
};
export type TDeleteWorkflow = ITypedReduxAction<EWorkflowsActions.DeleteWorkflow, TDeleteWorkflowPayload>;
export const deleteWorkflowAction: (payload: TDeleteWorkflowPayload) => TDeleteWorkflow = actionGenerator<
  EWorkflowsActions.DeleteWorkflow,
  TDeleteWorkflowPayload
>(EWorkflowsActions.DeleteWorkflow);

export type TReturnWorkflowToTaskPayload = {
  workflowId: number;
  taskId: number;
  onSuccess?(): void;
};
export type TReturnWorkflowToTask = ITypedReduxAction<
  EWorkflowsActions.ReturnWorkflowToTask,
  TReturnWorkflowToTaskPayload
>;
export const returnWorkflowToTaskAction: (payload: TReturnWorkflowToTaskPayload) => TReturnWorkflowToTask =
  actionGenerator<EWorkflowsActions.ReturnWorkflowToTask, TReturnWorkflowToTaskPayload>(
    EWorkflowsActions.ReturnWorkflowToTask,
  );

export type TCloneWorkflowPayload = {
  workflowId: number;
  workflowName: string;
  templateId?: number;
};
export type TCloneWorkflow = ITypedReduxAction<EWorkflowsActions.CloneWorkflow, TCloneWorkflowPayload>;
export const cloneWorkflowAction: (payload: TCloneWorkflowPayload) => TCloneWorkflow = actionGenerator<
  EWorkflowsActions.CloneWorkflow,
  TCloneWorkflowPayload
>(EWorkflowsActions.CloneWorkflow);

export type TUpdateCurrentPerformersCounters = ITypedReduxAction<
  EWorkflowsActions.UpdateCurrentPerformersCounters,
  void
>;
export const updateCurrentPerformersCounters: (payload?: void) => TUpdateCurrentPerformersCounters = actionGenerator<
  EWorkflowsActions.UpdateCurrentPerformersCounters,
  void
>(EWorkflowsActions.UpdateCurrentPerformersCounters);

export type TUpdateWorkflowStartersCounters = ITypedReduxAction<EWorkflowsActions.UpdateWorkflowStartersCounters, void>;
export const updateWorkflowStartersCounters: (payload?: void) => TUpdateWorkflowStartersCounters = actionGenerator<
  EWorkflowsActions.UpdateWorkflowStartersCounters,
  void
>(EWorkflowsActions.UpdateWorkflowStartersCounters);

export type TUpdateWorkflowsTemplateStepsCounters = ITypedReduxAction<
  EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters,
  void
>;
export const updateWorkflowsTemplateStepsCounters: (payload?: void) => TUpdateWorkflowsTemplateStepsCounters =
  actionGenerator<EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters, void>(
    EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters,
  );

export type TSnoozeWorkflowPayload = {
  workflowId: number;
  date: string;
  onSuccess?(workflow: IWorkflowClient): void;
};
export type TSnoozeWorkflow = ITypedReduxAction<EWorkflowsActions.SnoozeWorkflow, TSnoozeWorkflowPayload>;
export const snoozeWorkflow: (payload: TSnoozeWorkflowPayload) => TSnoozeWorkflow = actionGenerator<
  EWorkflowsActions.SnoozeWorkflow,
  TSnoozeWorkflowPayload
>(EWorkflowsActions.SnoozeWorkflow);

export type TDeleteCommentPayload = IDeleteComment;
export type TDeleteComment = ITypedReduxAction<EWorkflowsActions.DeleteComment, TDeleteCommentPayload>;
export const deleteComment: (payload: TDeleteCommentPayload) => TDeleteComment = actionGenerator<
  EWorkflowsActions.DeleteComment,
  TDeleteCommentPayload
>(EWorkflowsActions.DeleteComment);

export type TEditCommentPayload = IEditComment;
export type TEditComment = ITypedReduxAction<EWorkflowsActions.EditComment, TEditCommentPayload>;
export const editComment: (payload: TEditCommentPayload) => TEditComment = actionGenerator<
  EWorkflowsActions.EditComment,
  TEditCommentPayload
>(EWorkflowsActions.EditComment);

export type TSaveWorkflowsPreset = ITypedReduxAction<
  EWorkflowsActions.SaveWorkflowsPreset,
  { orderedFields: TOrderedFields[]; type: 'personal' | 'account'; templateId: number }
>;

export const saveWorkflowsPreset: (payload: {
  orderedFields: TOrderedFields[];
  type: 'personal' | 'account';
  templateId: number;
}) => TSaveWorkflowsPreset = actionGenerator<
  EWorkflowsActions.SaveWorkflowsPreset,
  { orderedFields: TOrderedFields[]; type: 'personal' | 'account'; templateId: number }
>(EWorkflowsActions.SaveWorkflowsPreset);

export type TWorkflowsActions =
  | TEditWorkflow
  | TSendWorkflowLogComment
  | TDeleteWorkflow
  | TReturnWorkflowToTask
  | TCloneWorkflow
  | TUpdateCurrentPerformersCounters
  | TUpdateWorkflowStartersCounters
  | TUpdateWorkflowsTemplateStepsCounters
  | TSnoozeWorkflow
  | TDeleteComment
  | TEditComment
  | TSaveWorkflowsPreset;

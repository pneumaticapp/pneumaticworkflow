import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import {
  TUserCounter,
  TTemplateStepCounter,
  EWorkflowsView,
  IWorkflowClient,
  IWorkflowDetailsClient,
} from '../../types/workflow';
import { IKickoff, TTemplatePreset, TOrderedFields } from '../../types/template';
import { TUploadedFile } from '../../utils/uploadFiles';
import { IDeleteComment } from '../../api/workflows/deleteComment';
import { IEditComment } from '../../api/workflows/editComment';
import { IWatchedComment } from '../../api/workflows/watchedComment';
import { ICreateReaction } from '../../api/workflows/createReactionComment';
import { IDeleteReaction } from '../../api/workflows/deleteReactionComment';

export const enum EWorkflowsActions {
  ResetWorkflowsList = 'RESET_WORKFLOWS_LIST',
  SetWorkflowFinished = 'SET_WORKFLOW_FINISHED',
  SetWorkflowResumed = 'SET_WORKFLOW_RESUMED',
  EditWorkflow = 'EDIT_WORKFLOW',
  EditWorkflowFail = 'EDIT_WORKFLOW_FAIL',
  EditWorkflowSuccess = 'EDIT_WORKFLOW_SUCCESS',
  ClearWorkflow = 'CLEAR_WORKFLOW',
  ApplyFilters = 'APPLY_WORKFLOWS_FITLERS',
  DeleteWorkflow = 'DELETE_WORKFLOW',
  ReturnWorkflowToTask = 'RETURN_WORKFLOW_TO_TASK',
  CloneWorkflow = 'CLONE_WORKFLOW',
  ToggleIsUrgent = 'TOGGLE_IS_URGENT',
  UpdateWorkflowStartersCounters = 'UPDATE_WORKFLOW_STARTERS_COUNTERS',
  SetWorkflowStartersCounters = 'SET_WORKFLOW_STARTERS_COUNTERS',
  SnoozeWorkflow = 'SNOOZE_WORKFLOW',
  PatchWorkflowInList = 'PATCH_WORKFLOW_IN_LIST',
  PatchWorkflowDetailed = 'PATCH_WORKFLOW_DETAILED',
  RemoveWorkflowFromList = 'REMOVE_WORKFLOW_FROM_LIST',
  SetWorkflowsView = 'SET_WORKFLOWS_VIEW',

  UpdateCurrentPerformersCounters = 'UPDATE_CURRENT_PERFORMERS_COUNTERS',
  SetCurrentPerformersCounters = 'SET_CURRENT_PERFORMERS_COUNTERS',

  SetWorkflowsTemplateStepsCounters = 'SET_WORKFLOW_TEMPLATE_STEPS_COUNTERS',
  UpdateWorkflowsTemplateStepsCounters = 'UPDATE_WORKFLOW_TEMPLATE_STEPS_COUNTERS',

  SetLoadingWorkflowLogComments = 'SET_LOADING_WORKFLOW_LOG_COMMENTS',
  SendWorkflowLogComment = 'SEND_WORKFLOW_LOG_COMMENT',
  DeleteComment = 'DELETE_COMMENT',
  EditComment = 'EDIT_COMMENT',
  WatchedComment = 'WATCHED_COMMENT',
  CreateReactionComment = 'CREATE_REACTION_COMMENT',
  DeleteReactionComment = 'DELETE_REACTION_COMMENT',

  OpenTuneViewModal = 'OPEN_TUNE_VIEW_MODAL',
  CloseTuneViewModal = 'CLOSE_TUNE_VIEW_MODAL',
  SetFilterSelectedFields = 'SET_WORKFLOWS_FILTER_SELECTED_FIELDS',
  SetLastLoadedTemplateId = 'SET_LAST_LOADED_TEMPLATE_ID',
  SetWorkflowsPresetsRedux = 'SET_WORKFLOWS_PRESETS_REDUX',
  SaveWorkflowsPreset = 'SAVE_WORKFLOWS_PRESET',
}

export type TDeleteReactionComment = ITypedReduxAction<EWorkflowsActions.DeleteReactionComment, IDeleteReaction>;
export const deleteReactionComment: (payload: IDeleteReaction) => TDeleteReactionComment = actionGenerator<
  EWorkflowsActions.DeleteReactionComment,
  IDeleteReaction
>(EWorkflowsActions.DeleteReactionComment);

export type TCreateReactionComment = ITypedReduxAction<EWorkflowsActions.CreateReactionComment, ICreateReaction>;
export const createReactionComment: (payload: ICreateReaction) => TCreateReactionComment = actionGenerator<
  EWorkflowsActions.CreateReactionComment,
  ICreateReaction
>(EWorkflowsActions.CreateReactionComment);

export type TWatchedComment = ITypedReduxAction<EWorkflowsActions.WatchedComment, IWatchedComment>;
export const watchedComment: (payload: IWatchedComment) => TWatchedComment = actionGenerator<
  EWorkflowsActions.WatchedComment,
  IWatchedComment
>(EWorkflowsActions.WatchedComment);

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

export type TEditWorkflowSuccess = ITypedReduxAction<EWorkflowsActions.EditWorkflowSuccess, void>;
export const editWorkflowSuccess: (payload?: void) => TEditWorkflowSuccess = actionGenerator<
  EWorkflowsActions.EditWorkflowSuccess,
  void
>(EWorkflowsActions.EditWorkflowSuccess);

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

export type TWorkflowResumed = ITypedReduxAction<EWorkflowsActions.SetWorkflowResumed, TSetWorkflowResumedPayload>;
export const setWorkflowResumed: (payload: TSetWorkflowResumedPayload) => TWorkflowResumed = actionGenerator<
  EWorkflowsActions.SetWorkflowResumed,
  TSetWorkflowResumedPayload
>(EWorkflowsActions.SetWorkflowResumed);

export type TSetWorkflowFinishedPayload = {
  workflowId: number;
  onWorkflowEnded?(): void;
};

export type TWorkflowFinished = ITypedReduxAction<EWorkflowsActions.SetWorkflowFinished, TSetWorkflowFinishedPayload>;
export const setWorkflowFinished: (payload: TSetWorkflowFinishedPayload) => TWorkflowFinished = actionGenerator<
  EWorkflowsActions.SetWorkflowFinished,
  TSetWorkflowFinishedPayload
>(EWorkflowsActions.SetWorkflowFinished);

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

export type TApplyWorkflowsFilters = ITypedReduxAction<EWorkflowsActions.ApplyFilters, void>;
export const applyWorkflowsFilters: (payload?: void) => TApplyWorkflowsFilters = actionGenerator<
  EWorkflowsActions.ApplyFilters,
  void
>(EWorkflowsActions.ApplyFilters);

export type TClearWorkflow = ITypedReduxAction<EWorkflowsActions.ClearWorkflow, void>;
export const clearWorkflow: (payload?: void) => TClearWorkflow = actionGenerator<EWorkflowsActions.ClearWorkflow, void>(
  EWorkflowsActions.ClearWorkflow,
);

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

export type TSetCurrentPerformersCounters = ITypedReduxAction<
  EWorkflowsActions.SetCurrentPerformersCounters,
  TUserCounter[]
>;
export const setCurrentPerformersCounters: (payload: TUserCounter[]) => TSetCurrentPerformersCounters = actionGenerator<
  EWorkflowsActions.SetCurrentPerformersCounters,
  TUserCounter[]
>(EWorkflowsActions.SetCurrentPerformersCounters);

export type TUpdateWorkflowStartersCounters = ITypedReduxAction<EWorkflowsActions.UpdateWorkflowStartersCounters, void>;
export const updateWorkflowStartersCounters: (payload?: void) => TUpdateWorkflowStartersCounters = actionGenerator<
  EWorkflowsActions.UpdateWorkflowStartersCounters,
  void
>(EWorkflowsActions.UpdateWorkflowStartersCounters);

export type TSetWorkflowStartersCounters = ITypedReduxAction<
  EWorkflowsActions.SetWorkflowStartersCounters,
  TUserCounter[]
>;
export const setWorkflowStartersCounters: (payload: TUserCounter[]) => TSetWorkflowStartersCounters = actionGenerator<
  EWorkflowsActions.SetWorkflowStartersCounters,
  TUserCounter[]
>(EWorkflowsActions.SetWorkflowStartersCounters);

export type TUpdateWorkflowsTemplateStepsCounters = ITypedReduxAction<
  EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters,
  void
>;
export const updateWorkflowsTemplateStepsCounters: (payload?: void) => TUpdateWorkflowsTemplateStepsCounters =
  actionGenerator<EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters, void>(
    EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters,
  );

export type TSetWorkflowsTemplateStepsCounters = ITypedReduxAction<
  EWorkflowsActions.SetWorkflowsTemplateStepsCounters,
  TTemplateStepCounter[]
>;
export const setWorkflowsTemplateStepsCounters: (
  payload: TTemplateStepCounter[],
) => TSetWorkflowsTemplateStepsCounters = actionGenerator<
  EWorkflowsActions.SetWorkflowsTemplateStepsCounters,
  TTemplateStepCounter[]
>(EWorkflowsActions.SetWorkflowsTemplateStepsCounters);

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

export type TPatchWorkflowInListPayload = {
  workflowId: number;
  changedFields: Partial<IWorkflowClient>;
};
export type TPatchWorkflowInList = ITypedReduxAction<
  EWorkflowsActions.PatchWorkflowInList,
  TPatchWorkflowInListPayload
>;
export const patchWorkflowInList: (payload: TPatchWorkflowInListPayload) => TPatchWorkflowInList = actionGenerator<
  EWorkflowsActions.PatchWorkflowInList,
  TPatchWorkflowInListPayload
>(EWorkflowsActions.PatchWorkflowInList);

export type TPatchWorkflowDetailedPayload = {
  workflowId: number;
  changedFields: Partial<IWorkflowDetailsClient>;
};
export type TPatchWorkflowDetailed = ITypedReduxAction<
  EWorkflowsActions.PatchWorkflowDetailed,
  TPatchWorkflowDetailedPayload
>;
export const patchWorkflowDetailed: (payload: TPatchWorkflowDetailedPayload) => TPatchWorkflowDetailed =
  actionGenerator<EWorkflowsActions.PatchWorkflowDetailed, TPatchWorkflowDetailedPayload>(
    EWorkflowsActions.PatchWorkflowDetailed,
  );

export type TRemoveWorkflowFromListPayload = {
  workflowId: number | null;
};
export type TRemoveWorkflowFromList = ITypedReduxAction<
  EWorkflowsActions.RemoveWorkflowFromList,
  TRemoveWorkflowFromListPayload
>;
export const removeWorkflowFromList: (payload: TRemoveWorkflowFromListPayload) => TRemoveWorkflowFromList =
  actionGenerator<EWorkflowsActions.RemoveWorkflowFromList, TRemoveWorkflowFromListPayload>(
    EWorkflowsActions.RemoveWorkflowFromList,
  );

export type TSetWorkflowsView = ITypedReduxAction<EWorkflowsActions.SetWorkflowsView, EWorkflowsView>;
export const setWorkflowsView: (payload: EWorkflowsView) => TSetWorkflowsView = actionGenerator<
  EWorkflowsActions.SetWorkflowsView,
  EWorkflowsView
>(EWorkflowsActions.SetWorkflowsView);

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

export type TOpenTuneViewModal = ITypedReduxAction<EWorkflowsActions.OpenTuneViewModal, void>;
export const openTuneViewModal: () => TOpenTuneViewModal = actionGenerator<EWorkflowsActions.OpenTuneViewModal, void>(
  EWorkflowsActions.OpenTuneViewModal,
);

export type TCloseTuneViewModal = ITypedReduxAction<EWorkflowsActions.CloseTuneViewModal, void>;
export const closeTuneViewModal: () => TCloseTuneViewModal = actionGenerator<EWorkflowsActions.CloseTuneViewModal>(
  EWorkflowsActions.CloseTuneViewModal,
);

export type TSetWorkflowsFilterSelectedFields = ITypedReduxAction<EWorkflowsActions.SetFilterSelectedFields, string[]>;

export const setWorkflowsFilterSelectedFields: (payload: string[]) => TSetWorkflowsFilterSelectedFields =
  actionGenerator<EWorkflowsActions.SetFilterSelectedFields, string[]>(EWorkflowsActions.SetFilterSelectedFields);

export type TSetLastLoadedTemplateId = ITypedReduxAction<EWorkflowsActions.SetLastLoadedTemplateId, string | null>;
export const setLastLoadedTemplateId: (payload: string | null) => TSetLastLoadedTemplateId = actionGenerator<
  EWorkflowsActions.SetLastLoadedTemplateId,
  string | null
>(EWorkflowsActions.SetLastLoadedTemplateId);

export type TSetWorkflowsPresetsRedux = ITypedReduxAction<
  EWorkflowsActions.SetWorkflowsPresetsRedux,
  TTemplatePreset[]
>;
export const setWorkflowsPresetsRedux: (presets: TTemplatePreset[]) => TSetWorkflowsPresetsRedux = actionGenerator<
  EWorkflowsActions.SetWorkflowsPresetsRedux,
  TTemplatePreset[]
>(EWorkflowsActions.SetWorkflowsPresetsRedux);

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
  | TWorkflowFinished
  | TEditWorkflow
  | TEditWorkflowSuccess
  | TSendWorkflowLogComment
  | TApplyWorkflowsFilters
  | TClearWorkflow
  | TDeleteWorkflow
  | TReturnWorkflowToTask
  | TCloneWorkflow
  | TUpdateCurrentPerformersCounters
  | TSetCurrentPerformersCounters
  | TUpdateWorkflowStartersCounters
  | TSetWorkflowStartersCounters
  | TUpdateWorkflowsTemplateStepsCounters
  | TSetWorkflowsTemplateStepsCounters
  | TSnoozeWorkflow
  | TPatchWorkflowInList
  | TPatchWorkflowDetailed
  | TRemoveWorkflowFromList
  | TSetWorkflowsView
  | TDeleteComment
  | TWatchedComment
  | TCreateReactionComment
  | TDeleteReactionComment
  | TEditComment
  | TOpenTuneViewModal
  | TCloseTuneViewModal
  | TSetWorkflowsFilterSelectedFields
  | TSetLastLoadedTemplateId
  | TSetWorkflowsPresetsRedux
  | TSaveWorkflowsPreset;

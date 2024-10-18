import { IWorkflowsList, ITypedReduxAction, IWorkflowLog } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import {
  EWorkflowsLogSorting,
  EWorkflowsSorting,
  IWorkflowDetails,
  IWorkflowEditData,
  EWorkflowsStatus,
  TUserCounter,
  TTemplateStepCounter,
  IWorkflow,
  EWorkflowsView,
  IWorkflowLogItem,
} from '../../types/workflow';
import { ITemplateTitle, IKickoff } from '../../types/template';
import { TUploadedFile } from '../../utils/uploadFiles';
import { ITemplateStep } from '../../types/tasks';
import { IDeleteComment } from '../../api/workflows/deleteComment';
import { IEditComment } from '../../api/workflows/editComment';
import { IWatchedComment } from '../../api/workflows/watchedComment';
import { ICreateReaction } from '../../api/workflows/createReactionComment';
import { IDeleteReaction } from '../../api/workflows/deleteReactionComment';

export const enum EWorkflowsActions {
  OpenWorkflowLogPopup = 'OPEN_WORKFLOW_LOG_POPUP',
  CloseWorkflowLogPopup = 'CLOSE_WORKFLOW_LOG_POPUP',
  ChangeWorkflowsList = 'CHANGE_WORKFLOWS_LIST',
  SetFilterStatus = 'CHANGE_WORKFLOWS_TYPE_SORTING',
  ChangeWorkflow = 'CHANGE_WORKFLOW',
  ChangeWorkflowLog = 'CHANGE_WORKFLOW_LOG',
  ChangeWorkflowsSearchText = 'CHANGE_WORKFLOWS_SEARCH_TEXT',
  ResetWorkflows = 'RESET_WORKFLOWS',
  ResetWorkflowsList = 'RESET_WORKFLOWS_LIST',
  ChangeWorkflowLogViewSettings = 'CHANGE_WORKFLOW_LOG_VIEW_SETTINGS',
  ChangeWorkflowsSorting = 'CHANGE_WORKFLOWS_SORTING',
  LoadWorkflowsList = 'LOAD_WORKFLOWS_LIST',
  LoadWorkflowsListFailed = 'LOAD_WORKFLOWS_LIST_FAILED',
  LoadWorkflow = 'LOAD_WORKFLOW',
  SetWorkflowIsLoading = 'SET_WORKFLOW_IS_LOADING',
  SetWorkflowFinished = 'SET_WORKFLOW_FINISHED',
  SetWorkflowResumed = 'SET_WORKFLOW_RESUMED',
  EditWorkflow = 'EDIT_WORKFLOW',
  EditWorkflowFail = 'EDIT_WORKFLOW_FAIL',
  EditWorkflowSuccess = 'EDIT_WORKFLOW_SUCCESS',
  SetIsEditWorkflowName = 'SET_IS_EDIT_WORKFLOW_NAME',
  SetIsEditKickoff = 'SET_IS_EDIT_KICKOFF',
  SetIsSavingWorkflowName = 'SET_IS_SAVING_WORKFLOW_NAME',
  SetIsSavingKickoff = 'SET_IS_SAVING_KICKOFF',
  SetWorkflowEdit = 'SET_WORKFLOW_EDIT',
  ClearWorkflow = 'CLEAR_WORKFLOW',
  LoadFilterTemplates = 'LOAD_WORKFLOWS_FITLER_TEMPLATES',
  LoadFilterTemplatesSuccess = 'LOAD_WORKFLOWS_FITLER_TEMPLATES_SUCCESS',
  LoadFilterTemplatesFailed = 'LOAD_WORKFLOWS_FITLER_TEMPLATES_FAILED',
  SetFilterTemplate = 'SET_WORKFLOWS_FILTER_TEMPLATE',
  SetFilterWorkflowStarters = 'SET_WORKFLOWS_FILTER_WORKFLOWS_STARTERS',
  ApplyFilters = 'APPLY_WORKFLOWS_FITLERS',
  ClearFilters = 'CLEAR_WORKFLOWS_FILTERS',
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
  UpdateWorkflowLogItem = 'UPDATE_WORKFLOW_LOG_ITEM',

  SetFilterPerformers =                   'SET_WORKFLOWS_FILTER_PERFORMERS',
  UpdateCurrentPerformersCounters =       'UPDATE_CURRENT_PERFORMERS_COUNTERS',
  SetCurrentPerformersCounters =          'SET_CURRENT_PERFORMERS_COUNTERS',

  SetFilterTemplateSteps =                'SET_WORKFLOWS_FILTER_TEMPLATE_STEPS',
  LoadFilterSteps =                       'LOAD_WORKFLOWS_FITLER_STEPS',
  LoadFilterStepsSuccess =                'LOAD_WORKFLOWS_FITLER_STEPS_SUCCESS',
  LoadFilterStepsFailed =                 'LOAD_WORKFLOWS_FITLER_STEPS_FAILED',
  SetWorkflowsTemplateStepsCounters =     'SET_WORKFLOW_TEMPLATE_STEPS_COUNTERS',
  UpdateWorkflowsTemplateStepsCounters =  'UPDATE_WORKFLOW_TEMPLATE_STEPS_COUNTERS',

  SetLoadingWorkflowLogComments =         'SET_LOADING_WORKFLOW_LOG_COMMENTS',
  SendWorkflowLogComment =                'SEND_WORKFLOW_LOG_COMMENT',
  DeleteComment =                         'DELETE_COMMENT',
  EditComment =                           'EDIT_COMMENT',
  WatchedComment =                        'WATCHED_COMMENT',
  CreateReactionComment =                 'CREATE_REACTION_COMMENT',
  DeleteReactionComment =                 'DELETE_REACTION_COMMENT',
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
  dueDate?: string;
}

export type TSetWorkflowIsLoading = ITypedReduxAction<EWorkflowsActions.SetWorkflowIsLoading, boolean>;
export const setWorkflowIsLoading: (payload: boolean) => TSetWorkflowIsLoading = actionGenerator<
  EWorkflowsActions.SetWorkflowIsLoading,
  boolean
>(EWorkflowsActions.SetWorkflowIsLoading);

export type TEditWorkflowSuccess = ITypedReduxAction<EWorkflowsActions.EditWorkflowSuccess, void>;
export const editWorkflowSuccess: (payload?: void) => TEditWorkflowSuccess = actionGenerator<
  EWorkflowsActions.EditWorkflowSuccess,
  void
>(EWorkflowsActions.EditWorkflowSuccess);

export type TEditWorkflowPayload = {
  name?: string;
  kickoff?: IKickoff | null;
  isUrgent?: boolean;
  dueDate?: string | null;
  workflowId: number;
};
export type TEditWorkflow = ITypedReduxAction<EWorkflowsActions.EditWorkflow, TEditWorkflowPayload>;
export const editWorkflow: (payload: TEditWorkflowPayload) => TEditWorkflow = actionGenerator<
  EWorkflowsActions.EditWorkflow,
  TEditWorkflowPayload
>(EWorkflowsActions.EditWorkflow);

export type TOpenWorkflowLogPopupPayload = {
  workflowId: number;
  redirectTo404IfNotFound?: boolean;
  shouldSetWorkflowDetailUrl?: boolean;
};

export type TOpenWorkflowLogPopup = ITypedReduxAction<
  EWorkflowsActions.OpenWorkflowLogPopup,
  TOpenWorkflowLogPopupPayload
>;
export const openWorkflowLogPopup: (payload: TOpenWorkflowLogPopupPayload) => TOpenWorkflowLogPopup = actionGenerator<
  EWorkflowsActions.OpenWorkflowLogPopup,
  TOpenWorkflowLogPopupPayload
>(EWorkflowsActions.OpenWorkflowLogPopup);

export type TCloseWorkflowLogPopup = ITypedReduxAction<EWorkflowsActions.CloseWorkflowLogPopup, void>;
export const closeWorkflowLogPopup: (payload?: void) => TCloseWorkflowLogPopup = actionGenerator<
  EWorkflowsActions.CloseWorkflowLogPopup,
  void
>(EWorkflowsActions.CloseWorkflowLogPopup);

export type TChangeWorkflow = ITypedReduxAction<EWorkflowsActions.ChangeWorkflow, IWorkflowDetails>;
export const changeWorkflow: (payload: IWorkflowDetails) => TChangeWorkflow = actionGenerator<
  EWorkflowsActions.ChangeWorkflow,
  IWorkflowDetails
>(EWorkflowsActions.ChangeWorkflow);

export type TChangeWorkflowLog = ITypedReduxAction<EWorkflowsActions.ChangeWorkflowLog, Partial<IWorkflowLog>>;
export const changeWorkflowLog: (payload: Partial<IWorkflowLog>) => TChangeWorkflowLog = actionGenerator<
  EWorkflowsActions.ChangeWorkflowLog,
  Partial<IWorkflowLog>
>(EWorkflowsActions.ChangeWorkflowLog);

export type TChangeWorkflowsSorting = ITypedReduxAction<EWorkflowsActions.ChangeWorkflowsSorting, EWorkflowsSorting>;
export const changeWorkflowsSorting: (payload: EWorkflowsSorting) => TChangeWorkflowsSorting = actionGenerator<
  EWorkflowsActions.ChangeWorkflowsSorting,
  EWorkflowsSorting
>(EWorkflowsActions.ChangeWorkflowsSorting);

export interface IChangeWorkflowLogViewSettingsPayload {
  id: number;
  sorting: EWorkflowsLogSorting;
  comments: boolean;
  isOnlyAttachmentsShown: boolean;
}

export type TChangeWorkflowLogViewSettings = ITypedReduxAction<
  EWorkflowsActions.ChangeWorkflowLogViewSettings,
  IChangeWorkflowLogViewSettingsPayload
>;
export const changeWorkflowLogViewSettings: (
  payload: IChangeWorkflowLogViewSettingsPayload,
) => TChangeWorkflowLogViewSettings = actionGenerator<
  EWorkflowsActions.ChangeWorkflowLogViewSettings,
  IChangeWorkflowLogViewSettingsPayload
>(EWorkflowsActions.ChangeWorkflowLogViewSettings);

export type TResetWorkflows = ITypedReduxAction<EWorkflowsActions.ResetWorkflows, void>;
export const resetWorkflows: (payload?: void) => TResetWorkflows = actionGenerator<
  EWorkflowsActions.ResetWorkflows,
  void
>(EWorkflowsActions.ResetWorkflows);

export type TLoadWorkflow = ITypedReduxAction<EWorkflowsActions.LoadWorkflow, number>;
export const loadWorkflow: (payload: number) => TLoadWorkflow = actionGenerator<EWorkflowsActions.LoadWorkflow, number>(
  EWorkflowsActions.LoadWorkflow,
);

export type TChangeWorkflowsList = ITypedReduxAction<EWorkflowsActions.ChangeWorkflowsList, IWorkflowsList>;
export const changeWorkflowsList: (payload: IWorkflowsList) => TChangeWorkflowsList = actionGenerator<
  EWorkflowsActions.ChangeWorkflowsList,
  IWorkflowsList
>(EWorkflowsActions.ChangeWorkflowsList);

export type TLoadWorkflowsList = ITypedReduxAction<EWorkflowsActions.LoadWorkflowsList, number>;
export const loadWorkflowsList: (payload: number) => TLoadWorkflowsList = actionGenerator<
  EWorkflowsActions.LoadWorkflowsList,
  number
>(EWorkflowsActions.LoadWorkflowsList);

export type TLoadWorkflowsListFailed = ITypedReduxAction<EWorkflowsActions.LoadWorkflowsListFailed, void>;
export const loadWorkflowsListFailed: (payload?: void) => TLoadWorkflowsListFailed = actionGenerator<
  EWorkflowsActions.LoadWorkflowsListFailed,
  void
>(EWorkflowsActions.LoadWorkflowsListFailed);

export type TChangeWorkflowsSearchText = ITypedReduxAction<EWorkflowsActions.ChangeWorkflowsSearchText, string>;
export const changeWorkflowsSearchText: (payload: string) => TChangeWorkflowsSearchText = actionGenerator<
  EWorkflowsActions.ChangeWorkflowsSearchText,
  string
>(EWorkflowsActions.ChangeWorkflowsSearchText);

export type TSetWorkflowsFilterStatus = ITypedReduxAction<EWorkflowsActions.SetFilterStatus, EWorkflowsStatus>;
export const setWorkflowsFilterStatus: (payload: EWorkflowsStatus) => TSetWorkflowsFilterStatus = actionGenerator<
  EWorkflowsActions.SetFilterStatus,
  EWorkflowsStatus
>(EWorkflowsActions.SetFilterStatus);

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

export type TLoadWorkflowsFilterTemplates = ITypedReduxAction<EWorkflowsActions.LoadFilterTemplates, void>;
export const loadWorkflowsFilterTemplates: (payload?: void) => TLoadWorkflowsFilterTemplates = actionGenerator<
  EWorkflowsActions.LoadFilterTemplates,
  void
>(EWorkflowsActions.LoadFilterTemplates);

export type TLoadWorkflowsFilterTemplatesSuccess = ITypedReduxAction<
  EWorkflowsActions.LoadFilterTemplatesSuccess,
  ITemplateTitle[]
>;
export const loadWorkflowsFilterTemplatesSuccess: (payload: ITemplateTitle[]) => TLoadWorkflowsFilterTemplatesSuccess =
  actionGenerator<EWorkflowsActions.LoadFilterTemplatesSuccess, ITemplateTitle[]>(
    EWorkflowsActions.LoadFilterTemplatesSuccess,
  );

export type TLoadWorkflowsFilterTemplatesFailed = ITypedReduxAction<EWorkflowsActions.LoadFilterTemplatesFailed, void>;
export const loadWorkflowsFilterTemplatesFailed: (payload?: void) => TLoadWorkflowsFilterTemplatesFailed =
  actionGenerator<EWorkflowsActions.LoadFilterTemplatesFailed, void>(EWorkflowsActions.LoadFilterTemplatesFailed);

export type TSetWorkflowsFilterTemplate = ITypedReduxAction<EWorkflowsActions.SetFilterTemplate, number[]>;
export const setWorkflowsFilterTemplate: (payload: number[]) => TSetWorkflowsFilterTemplate = actionGenerator<
  EWorkflowsActions.SetFilterTemplate,
  number[]
>(EWorkflowsActions.SetFilterTemplate);

export type TLoadWorkflowsFilterStepsPayload = {
  templateId: number;
  onAfterLoaded?(steps: ITemplateStep[]): void;
};
export type TLoadWorkflowsFilterSteps = ITypedReduxAction<
  EWorkflowsActions.LoadFilterSteps,
  TLoadWorkflowsFilterStepsPayload
>;
export const loadWorkflowsFilterSteps: (payload: TLoadWorkflowsFilterStepsPayload) => TLoadWorkflowsFilterSteps =
  actionGenerator<EWorkflowsActions.LoadFilterSteps, TLoadWorkflowsFilterStepsPayload>(
    EWorkflowsActions.LoadFilterSteps,
  );

type TLoadWorkflowsFilterStepsSuccessPayload = {
  templateId: number;
  steps: ITemplateStep[];
};
export type TLoadWorkflowsFilterStepsSuccess = ITypedReduxAction<
  EWorkflowsActions.LoadFilterStepsSuccess,
  TLoadWorkflowsFilterStepsSuccessPayload
>;
export const loadWorkflowsFilterStepsSuccess: (
  payload: TLoadWorkflowsFilterStepsSuccessPayload,
) => TLoadWorkflowsFilterStepsSuccess = actionGenerator<
  EWorkflowsActions.LoadFilterStepsSuccess,
  TLoadWorkflowsFilterStepsSuccessPayload
>(EWorkflowsActions.LoadFilterStepsSuccess);

type TLoadWorkflowsFilterStepsFailedPayload = { templateId: number };
export type TLoadWorkflowsFilterStepsFailed = ITypedReduxAction<
  EWorkflowsActions.LoadFilterStepsFailed,
  TLoadWorkflowsFilterStepsFailedPayload
>;
export const loadWorkflowsFilterStepsFailed: (
  payload: TLoadWorkflowsFilterStepsFailedPayload,
) => TLoadWorkflowsFilterStepsFailed = actionGenerator<
  EWorkflowsActions.LoadFilterStepsFailed,
  TLoadWorkflowsFilterStepsFailedPayload
>(EWorkflowsActions.LoadFilterStepsFailed);

export type TSetWorkflowsFilterSteps = ITypedReduxAction<EWorkflowsActions.SetFilterTemplateSteps, number[]>;
export const setWorkflowsFilterSteps: (payload: number[]) => TSetWorkflowsFilterSteps = actionGenerator<
  EWorkflowsActions.SetFilterTemplateSteps,
  number[]
>(EWorkflowsActions.SetFilterTemplateSteps);

export type TSetWorkflowsFilterPerfomers = ITypedReduxAction<EWorkflowsActions.SetFilterPerformers, number[]>;
export const setWorkflowsFilterPerfomers: (payload: number[]) => TSetWorkflowsFilterPerfomers = actionGenerator<
  EWorkflowsActions.SetFilterPerformers,
  number[]
>(EWorkflowsActions.SetFilterPerformers);

export type TSetWorkflowsFilterWorkflowStarters = ITypedReduxAction<
  EWorkflowsActions.SetFilterWorkflowStarters,
  number[]
>;
export const setWorkflowsFilterWorkflowStarters: (payload: number[]) => TSetWorkflowsFilterWorkflowStarters =
  actionGenerator<EWorkflowsActions.SetFilterWorkflowStarters, number[]>(EWorkflowsActions.SetFilterWorkflowStarters);

export interface ISendWorkflowLogComment {
  text: string;
  attachments: TUploadedFile[];
}

export type TSendWorkflowLogComment = ITypedReduxAction<
  EWorkflowsActions.SendWorkflowLogComment,
  ISendWorkflowLogComment
>;

export const sendWorkflowLogComments: (payload: ISendWorkflowLogComment) => TSendWorkflowLogComment = actionGenerator<
  EWorkflowsActions.SendWorkflowLogComment,
  ISendWorkflowLogComment
>(EWorkflowsActions.SendWorkflowLogComment);

export type TSetIsEditWorkflowName = ITypedReduxAction<EWorkflowsActions.SetIsEditWorkflowName, boolean>;
export const setIsEditWorkflowName: (payload: boolean) => TSetIsEditWorkflowName = actionGenerator<
  EWorkflowsActions.SetIsEditWorkflowName,
  boolean
>(EWorkflowsActions.SetIsEditWorkflowName);

export type TSetIsEditKickoff = ITypedReduxAction<EWorkflowsActions.SetIsEditKickoff, boolean>;
export const setIsEditKickoff: (payload: boolean) => TSetIsEditKickoff = actionGenerator<
  EWorkflowsActions.SetIsEditKickoff,
  boolean
>(EWorkflowsActions.SetIsEditKickoff);

export type TSetIsSavingWorkflowName = ITypedReduxAction<EWorkflowsActions.SetIsSavingWorkflowName, boolean>;
export const setIsSavingWorkflowName: (payload: boolean) => TSetIsSavingWorkflowName = actionGenerator<
  EWorkflowsActions.SetIsSavingWorkflowName,
  boolean
>(EWorkflowsActions.SetIsSavingWorkflowName);

export type TSetIsSavingKickoff = ITypedReduxAction<EWorkflowsActions.SetIsSavingKickoff, boolean>;
export const setIsSavingKickoff: (payload: boolean) => TSetIsSavingKickoff = actionGenerator<
  EWorkflowsActions.SetIsSavingKickoff,
  boolean
>(EWorkflowsActions.SetIsSavingKickoff);

export type TSetWorkflowEdit = ITypedReduxAction<EWorkflowsActions.SetWorkflowEdit, IWorkflowEditData>;
export const setWorkflowEdit: (payload: IWorkflowEditData) => TSetWorkflowEdit = actionGenerator<
  EWorkflowsActions.SetWorkflowEdit,
  IWorkflowEditData
>(EWorkflowsActions.SetWorkflowEdit);

export type TClearWorkflowsFilters = ITypedReduxAction<EWorkflowsActions.ClearFilters, void>;
export const clearWorkflowsFilters: (payload?: void) => TClearWorkflowsFilters = actionGenerator<
  EWorkflowsActions.ClearFilters,
  void
>(EWorkflowsActions.ClearFilters);

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
  onSuccess?(workflow: IWorkflowDetails): void;
};
export type TSnoozeWorkflow = ITypedReduxAction<EWorkflowsActions.SnoozeWorkflow, TSnoozeWorkflowPayload>;
export const snoozeWorkflow: (payload: TSnoozeWorkflowPayload) => TSnoozeWorkflow = actionGenerator<
  EWorkflowsActions.SnoozeWorkflow,
  TSnoozeWorkflowPayload
>(EWorkflowsActions.SnoozeWorkflow);

export type TPatchWorkflowInListPayload = {
  workflowId: number;
  changedFields: Partial<IWorkflow>;
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
  changedFields: Partial<IWorkflowDetails>;
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

export type TUpdateWorkflowLogItemPayload = IWorkflowLogItem;
export type TUpdateWorkflowLogItem = ITypedReduxAction<
  EWorkflowsActions.UpdateWorkflowLogItem,
  TUpdateWorkflowLogItemPayload
>;
export const updateWorkflowLogItem: (payload: TUpdateWorkflowLogItemPayload) => TUpdateWorkflowLogItem =
  actionGenerator<EWorkflowsActions.UpdateWorkflowLogItem, TUpdateWorkflowLogItemPayload>(
    EWorkflowsActions.UpdateWorkflowLogItem,
  );

export type TEditCommentPayload = IEditComment;
export type TEditComment = ITypedReduxAction<EWorkflowsActions.EditComment, TEditCommentPayload>;
export const editComment: (payload: TEditCommentPayload) => TEditComment = actionGenerator<
  EWorkflowsActions.EditComment,
  TEditCommentPayload
>(EWorkflowsActions.EditComment);

export type TWorkflowsActions =
  | TOpenWorkflowLogPopup
  | TChangeWorkflowsList
  | TSetWorkflowsFilterStatus
  | TChangeWorkflow
  | TChangeWorkflowLog
  | TChangeWorkflowsSearchText
  | TChangeWorkflowLogViewSettings
  | TCloseWorkflowLogPopup
  | TLoadWorkflowsList
  | TLoadWorkflowsListFailed
  | TLoadWorkflow
  | TChangeWorkflowsSorting
  | TSetWorkflowIsLoading
  | TWorkflowFinished
  | TEditWorkflow
  | TEditWorkflowSuccess
  | TLoadWorkflowsFilterTemplates
  | TLoadWorkflowsFilterTemplatesSuccess
  | TLoadWorkflowsFilterTemplatesFailed
  | TSetWorkflowsFilterTemplate
  | TLoadWorkflowsFilterSteps
  | TLoadWorkflowsFilterStepsSuccess
  | TLoadWorkflowsFilterStepsFailed
  | TSetWorkflowsFilterSteps
  | TSetWorkflowsFilterPerfomers
  | TSetWorkflowsFilterWorkflowStarters
  | TSendWorkflowLogComment
  | TSetIsEditWorkflowName
  | TSetIsEditKickoff
  | TSetWorkflowEdit
  | TSetIsSavingKickoff
  | TSetIsSavingWorkflowName
  | TResetWorkflows
  | TApplyWorkflowsFilters
  | TClearWorkflow
  | TDeleteWorkflow
  | TReturnWorkflowToTask
  | TCloneWorkflow
  | TUpdateCurrentPerformersCounters
  | TSetCurrentPerformersCounters
  | TUpdateWorkflowStartersCounters
  | TSetWorkflowStartersCounters
  | TClearWorkflowsFilters
  | TUpdateWorkflowsTemplateStepsCounters
  | TSetWorkflowsTemplateStepsCounters
  | TSnoozeWorkflow
  | TPatchWorkflowInList
  | TPatchWorkflowDetailed
  | TRemoveWorkflowFromList
  | TSetWorkflowsView
  | TDeleteComment
  | TUpdateWorkflowLogItem
  | TWatchedComment
  | TCreateReactionComment
  | TDeleteReactionComment
  | TEditComment;

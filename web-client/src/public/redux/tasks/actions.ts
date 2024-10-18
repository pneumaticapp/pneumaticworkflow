import {
  ITaskList,
  ITypedReduxAction,
} from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { ETaskListCompletionStatus, ETaskListSorting, ITaskListItem, ITemplateStep } from '../../types/tasks';
import { ITemplateTitle } from '../../types/template';
import { ETaskListStatus } from '../../components/Tasks/types';

export const enum ETaskListActions {
  ChannelAction = 'TASK_LIST_CHANNEL_ACTION',
  ChangeTaskList = 'CHANGE_TASK_LIST',
  SetTaskListDetailedTaskId = 'SET_TASK_LIST_DETAILED_TASK_ID',
  ChangeTasksSearchText = 'CHANGE_TASKS_SEARCH_TEXT',
  SearchTasks = 'SEARCH_TASKS',
  ResetTasks = 'RESET_TASKS',
  ResetTasksFilters = 'RESET_TASKS_FILTERS',
  ChangeTaskListSorting = 'CHANGE_TASK_LIST_SORTING',
  ChangeTaskListСompletionStatus = 'CHANGE_TASK_LIST_COMPLETION_STATUS',
  ChangeTasksCount = 'CHANGE_TASKS_COUNT',
  LoadTasksCount = 'LOAD_TASKS_COUNT',
  LoadTaskList = 'LOAD_TASK_LIST',
  ShowNewTasksNotification = 'SHOW_NEW_TASK_NOTIFICATION',
  InsertNewTask = 'INSERT_NEW_TASK',
  SetTaskListStatus = 'SET_TASK_LIST_STATUS',

  LoadFilterTemplates = 'LOAD_TASKS_FITLER_TEMPLATES',
  LoadFilterTemplatesSuccess = 'LOAD_TASKS_FITLER_TEMPLATES_SUCCESS',
  LoadFilterTemplatesFailed = 'LOAD_TASKS_FITLER_TEMPLATES_FAILED',
  SetFilterTemplate = 'SET_TASKS_FILTER_TEMPLATE',

  LoadFilterSteps = 'LOAD_TASKS_FILTER_TEMPLATE_STEPS',
  LoadFilterStepsSuccess = 'LOAD_TASKS_FILTER_TEMPLATE_STEPS_SUCCESS',
  LoadFilterStepsFailed = 'LOAD_TASKS_FILTER_TEMPLATE_STEPS_FAILED',
  SetFilterStep = 'SET_TASKS_FILTER_TEMPLATE_STEP',
  ClearFilters = 'CLEAR_TASKS_FILTERS',

  ShiftTaskList = 'SHIFT_TASK_LIST',
  PatchTaskInList = 'PATCH_TASK_IN_LIST',
}

export type TChangeTaskListSorting = ITypedReduxAction<ETaskListActions.ChangeTaskListSorting, ETaskListSorting>;
export const changeTasksSorting: (payload: ETaskListSorting) => TChangeTaskListSorting =
  actionGenerator<ETaskListActions.ChangeTaskListSorting, ETaskListSorting>(ETaskListActions.ChangeTaskListSorting);

export type TChangeTaskListCompletionStatus =
  ITypedReduxAction<ETaskListActions.ChangeTaskListСompletionStatus, ETaskListCompletionStatus>;
export const changeTasksCompleteStatus: (payload: ETaskListCompletionStatus) => TChangeTaskListCompletionStatus =
  actionGenerator<ETaskListActions.ChangeTaskListСompletionStatus, ETaskListCompletionStatus>
  (ETaskListActions.ChangeTaskListСompletionStatus);

export type TResetTasks = ITypedReduxAction<ETaskListActions.ResetTasks, void>;
export const resetTasks: (payload?: void) => TResetTasks =
  actionGenerator<ETaskListActions.ResetTasks, void>(ETaskListActions.ResetTasks);

export type TResetTasksFilters = ITypedReduxAction<ETaskListActions.ResetTasksFilters, void>;
export const resetTasksFilters: (payload?: void) => TResetTasksFilters =
  actionGenerator<ETaskListActions.ResetTasksFilters, void>(ETaskListActions.ResetTasksFilters);

type TChangeTaskListPayload = {
  taskList: ITaskList;
  emptyListStatus?: ETaskListStatus;
};
export type TChangeTaskList = ITypedReduxAction<ETaskListActions.ChangeTaskList, TChangeTaskListPayload>;
export const changeTaskList: (payload: TChangeTaskListPayload) => TChangeTaskList =
  actionGenerator<ETaskListActions.ChangeTaskList, TChangeTaskListPayload>
  (ETaskListActions.ChangeTaskList);

type TPatchTaskInListPayload = {
  taskId: number;
  task: Partial<ITaskListItem>
};

export type TPatchTaskInList = ITypedReduxAction<ETaskListActions.PatchTaskInList, TPatchTaskInListPayload>;
export const patchTaskInList: (payload: TPatchTaskInListPayload) => TPatchTaskInList =
  actionGenerator<ETaskListActions.PatchTaskInList, TPatchTaskInListPayload>
  (ETaskListActions.PatchTaskInList);

export type TSetTaskListDetailedTaskId = ITypedReduxAction<ETaskListActions.SetTaskListDetailedTaskId, number>;
export const setTaskListDetailedTaskId: (payload: number) => TSetTaskListDetailedTaskId =
  actionGenerator<ETaskListActions.SetTaskListDetailedTaskId, number>
  (ETaskListActions.SetTaskListDetailedTaskId);

export type TChangeTasksSearchText = ITypedReduxAction<ETaskListActions.ChangeTasksSearchText, string>;
export const changeTasksSearchText: (payload: string) => TChangeTasksSearchText =
  actionGenerator<ETaskListActions.ChangeTasksSearchText, string>
  (ETaskListActions.ChangeTasksSearchText);

export type TLoadTasksCount = ITypedReduxAction<ETaskListActions.LoadTasksCount, void>;
export const loadTasksCount: (payload?: void) => TLoadTasksCount =
  actionGenerator<ETaskListActions.LoadTasksCount, void>(ETaskListActions.LoadTasksCount);

export type TChangeTasksCount = ITypedReduxAction<ETaskListActions.ChangeTasksCount, number>;
export const changeTasksCount: (payload: number) => TChangeTasksCount =
  actionGenerator<ETaskListActions.ChangeTasksCount, number>(ETaskListActions.ChangeTasksCount);

export type TLoadTaskList = ITypedReduxAction<ETaskListActions.LoadTaskList, number>;
export const loadTaskList: (payload: number) => TLoadTaskList =
  actionGenerator<ETaskListActions.LoadTaskList, number>(ETaskListActions.LoadTaskList);

export type TLoadTasksFilterTemplates = ITypedReduxAction<ETaskListActions.LoadFilterTemplates, void>;
export const loadTasksFilterTemplates: (payload?: void) => TLoadTasksFilterTemplates =
  actionGenerator<ETaskListActions.LoadFilterTemplates, void>(ETaskListActions.LoadFilterTemplates);

export type TLoadTasksFilterTemplatesSuccess = ITypedReduxAction<ETaskListActions.LoadFilterTemplatesSuccess, ITemplateTitle[]>;
export const loadTasksFilterTemplatesSuccess: (payload: ITemplateTitle[]) => TLoadTasksFilterTemplatesSuccess =
  actionGenerator<ETaskListActions.LoadFilterTemplatesSuccess, ITemplateTitle[]>(ETaskListActions.LoadFilterTemplatesSuccess);

export type TLoadTasksFilterTemplatesFailed = ITypedReduxAction<ETaskListActions.LoadFilterTemplatesFailed, void>;
export const loadTasksFilterTemplatesFailed: (payload?: void) => TLoadTasksFilterTemplatesFailed =
  actionGenerator<ETaskListActions.LoadFilterTemplatesFailed, void>(ETaskListActions.LoadFilterTemplatesFailed);

export type TSetTasksFilterTemplate = ITypedReduxAction<ETaskListActions.SetFilterTemplate, number | null>;
export const setTasksFilterTemplate: (payload: number | null) => TSetTasksFilterTemplate =
  actionGenerator<ETaskListActions.SetFilterTemplate, number | null>(ETaskListActions.SetFilterTemplate);

export type TLoadTasksFilterStepsPayload = { templateId: number };
export type TLoadTasksFilterSteps = ITypedReduxAction<ETaskListActions.LoadFilterSteps, TLoadTasksFilterStepsPayload>;
export const loadTasksFilterSteps: (payload: TLoadTasksFilterStepsPayload) => TLoadTasksFilterSteps =
  actionGenerator<ETaskListActions.LoadFilterSteps, TLoadTasksFilterStepsPayload>(ETaskListActions.LoadFilterSteps);

export type TLoadTasksFilterStepsSuccess = ITypedReduxAction<ETaskListActions.LoadFilterStepsSuccess, ITemplateStep[]>;
export const loadTasksFilterStepsSuccess: (payload: ITemplateStep[]) => TLoadTasksFilterStepsSuccess =
  actionGenerator<ETaskListActions.LoadFilterStepsSuccess, ITemplateStep[]>(ETaskListActions.LoadFilterStepsSuccess);

export type TLoadTasksFilterStepsFailed = ITypedReduxAction<ETaskListActions.LoadFilterStepsFailed, void>;
export const loadTasksFilterStepsFailed: (payload?: void) => TLoadTasksFilterStepsFailed =
  actionGenerator<ETaskListActions.LoadFilterStepsFailed, void>(ETaskListActions.LoadFilterStepsFailed);

export type TSetTasksFilterStep = ITypedReduxAction<ETaskListActions.SetFilterStep, number | null>;
export const setTasksFilterStep: (payload: number | null) => TSetTasksFilterStep =
  actionGenerator<ETaskListActions.SetFilterStep, number | null>(ETaskListActions.SetFilterStep);

export type TShowNewTasksNotification = ITypedReduxAction<ETaskListActions.ShowNewTasksNotification, boolean>;
export const showNewTasksNotification: (payload: boolean) => TShowNewTasksNotification =
  actionGenerator<ETaskListActions.ShowNewTasksNotification, boolean>(ETaskListActions.ShowNewTasksNotification);

export type TInsertNewTask = ITypedReduxAction<ETaskListActions.InsertNewTask, ITaskListItem>;
export const insertNewTask: (payload: ITaskListItem) => TInsertNewTask =
  actionGenerator<ETaskListActions.InsertNewTask, ITaskListItem>(ETaskListActions.InsertNewTask);

export type TClearTasksFilters = ITypedReduxAction<ETaskListActions.ClearFilters, void>;
export const clearTasksFilters: (payload?: void) => TClearTasksFilters =
  actionGenerator<ETaskListActions.ClearFilters, void>(ETaskListActions.ClearFilters);

export type TSetTaskListStatus = ITypedReduxAction<ETaskListActions.SetTaskListStatus, ETaskListStatus>;
export const setTaskListStatus: (payload: ETaskListStatus) => TSetTaskListStatus =
  actionGenerator<ETaskListActions.SetTaskListStatus, ETaskListStatus>(ETaskListActions.SetTaskListStatus);

export type TSearchTasks = ITypedReduxAction<ETaskListActions.SearchTasks, void>;
export const searchTasks: (payload?: void) => TSearchTasks =
  actionGenerator<ETaskListActions.SearchTasks, void>(ETaskListActions.SearchTasks);

export type TShiftTaskListPayload = { currentTaskId: number };
export type TShiftTaskList = ITypedReduxAction<ETaskListActions.ShiftTaskList, TShiftTaskListPayload>;
export const shiftTaskList: (payload: TShiftTaskListPayload) => TShiftTaskList =
  actionGenerator<ETaskListActions.ShiftTaskList, TShiftTaskListPayload>(ETaskListActions.ShiftTaskList);

export type TTaskListActions =
  | TChangeTaskListSorting
  | TChangeTaskListCompletionStatus
  | TResetTasks
  | TResetTasksFilters
  | TChangeTaskList
  | TSetTaskListDetailedTaskId
  | TChangeTasksSearchText
  | TLoadTasksCount
  | TChangeTasksCount
  | TLoadTaskList
  | TLoadTasksFilterTemplates
  | TLoadTasksFilterTemplatesSuccess
  | TLoadTasksFilterTemplatesFailed
  | TSetTasksFilterTemplate
  | TLoadTasksFilterSteps
  | TLoadTasksFilterStepsSuccess
  | TLoadTasksFilterStepsFailed
  | TSetTasksFilterStep
  | TShowNewTasksNotification
  | TInsertNewTask
  | TLoadTasksFilterTemplates
  | TSetTasksFilterTemplate
  | TClearTasksFilters
  | TSetTaskListStatus
  | TSearchTasks
  | TShiftTaskList
  | TPatchTaskInList;

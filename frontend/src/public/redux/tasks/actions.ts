import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { ITaskListItem } from '../../types/tasks';

export const enum ETaskListActions {
  ChannelAction = 'TASK_LIST_CHANNEL_ACTION',
  SearchTasks = 'SEARCH_TASKS',
  LoadTasksCount = 'LOAD_TASKS_COUNT',
  LoadTaskList = 'LOAD_TASK_LIST',
  InsertNewTask = 'INSERT_NEW_TASK',
  ShiftTaskList = 'SHIFT_TASK_LIST',
}

export type TLoadTasksCount = ITypedReduxAction<ETaskListActions.LoadTasksCount, void>;
export const loadTasksCount: (payload?: void) => TLoadTasksCount = actionGenerator<
  ETaskListActions.LoadTasksCount,
  void
>(ETaskListActions.LoadTasksCount);

export type TLoadTaskList = ITypedReduxAction<ETaskListActions.LoadTaskList, number>;
export const loadTaskList: (payload: number) => TLoadTaskList = actionGenerator<ETaskListActions.LoadTaskList, number>(
  ETaskListActions.LoadTaskList,
);

export type TInsertNewTask = ITypedReduxAction<ETaskListActions.InsertNewTask, ITaskListItem>;
export const insertNewTask: (payload: ITaskListItem) => TInsertNewTask = actionGenerator<
  ETaskListActions.InsertNewTask,
  ITaskListItem
>(ETaskListActions.InsertNewTask);

export type TSearchTasks = ITypedReduxAction<ETaskListActions.SearchTasks, void>;
export const searchTasks: (payload?: void) => TSearchTasks = actionGenerator<ETaskListActions.SearchTasks, void>(
  ETaskListActions.SearchTasks,
);

export type TShiftTaskListPayload = { currentTaskId: number };
export type TShiftTaskList = ITypedReduxAction<ETaskListActions.ShiftTaskList, TShiftTaskListPayload>;
export const shiftTaskList: (payload: TShiftTaskListPayload) => TShiftTaskList = actionGenerator<
  ETaskListActions.ShiftTaskList,
  TShiftTaskListPayload
>(ETaskListActions.ShiftTaskList);

export type TTaskListActions = TLoadTasksCount | TLoadTaskList | TInsertNewTask | TSearchTasks | TShiftTaskList;

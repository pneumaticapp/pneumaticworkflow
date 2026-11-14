import type { ITaskListItem, ITasksSettings } from '../../types/tasks';

export enum ETaskListStatus {
  WaitingForAction = 'waiting-for-action',
  Loading = 'loading',
  Searching = 'searching',
  NoTasks = 'no-tasks',
  EmptySearchResult = 'empty-search-result',
  LastTaskFinished = 'last-task-finished',
  LastFilteredTaskFinished = 'last-filtered-task-finished',
}

export interface ITaskList {
  count: number;
  offset: number;
  items: ITaskListItem[];
}

export interface IStoreTasks {
  taskList: ITaskList;
  taskListDetailedTaskId: number | null;
  tasksSearchText: string;
  tasksSettings: ITasksSettings;
  taskListStatus: ETaskListStatus;
  tasksCount: number | null;
  hasNewTasks: boolean;
}

export type TLoadFilterStepsPayload = { templateId: number };

export type TPatchTaskInListPayload = {
  taskId: number;
  task: Partial<ITaskListItem>;
};

export type TShiftTaskListPayload = { currentTaskId: number };

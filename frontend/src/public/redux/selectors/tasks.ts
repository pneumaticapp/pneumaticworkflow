import { IApplicationState, IStoreTasks, ITaskList } from '../../types/redux';
import { ETaskListCompleteSorting, ETaskListSorting, ITaskListItem, ITasksSettings } from '../../types/tasks';

export const getTasksSearchText = (state: IApplicationState): string => state.tasks.tasksSearchText;
export const getTasksStore = (state: IApplicationState): IStoreTasks => state.tasks;
export const getTaskList = (state: IApplicationState): ITaskList => {
  return state.tasks.taskList;
};
export const getTaskListItems = (state: IApplicationState): ITaskListItem[] => {
  return state.tasks.taskList.items;
};

export const getTasksSettings = (state: IApplicationState): ITasksSettings => {
  return state.tasks.tasksSettings;
};
export const getTasksSorting = (state: IApplicationState): ETaskListSorting | ETaskListCompleteSorting => {
  return state.tasks.tasksSettings.sorting;
};
export const getTotalTasksCount = (state: IApplicationState): number | null => {
  return state.tasks.tasksCount;
};

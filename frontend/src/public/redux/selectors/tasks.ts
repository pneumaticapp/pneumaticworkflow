import { IStoreTasks, ITaskList } from '../../types/redux';
import type { RootState } from '../store';
import { ETaskListCompleteSorting, ETaskListSorting, ITaskListItem, ITasksSettings } from '../../types/tasks';

export const getTasksSearchText = (state: RootState): string => state.tasks.tasksSearchText;
export const getTasksStore = (state: RootState): IStoreTasks => state.tasks;
export const getTaskList = (state: RootState): ITaskList => {
  return state.tasks.taskList;
};
export const getTaskListItems = (state: RootState): ITaskListItem[] => {
  return state.tasks.taskList.items;
};

export const getTasksSettings = (state: RootState): ITasksSettings => {
  return state.tasks.tasksSettings;
};
export const getTasksSorting = (state: RootState): ETaskListSorting | ETaskListCompleteSorting => {
  return state.tasks.tasksSettings.sorting;
};
export const getTotalTasksCount = (state: RootState): number | null => {
  return state.tasks.tasksCount;
};

export const getTasksFilterTemplatesIsLoading = (state: RootState): boolean =>
  state.tasks.tasksSettings.templateList.isLoading;

export const getTasksFilterStepsIsLoading = (state: RootState): boolean =>
  state.tasks.tasksSettings.templateStepList.isLoading;

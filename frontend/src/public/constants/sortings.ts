import {
  EWorkflowLogAttachmentsModes,
  EWorkflowsLogSorting,
  ETemplatesSorting,
} from '../types/workflow';
import { ETaskListCompleteSorting, ETaskListSorting } from '../types/tasks';
import { EGroupsListSorting, EUserListSorting } from '../types/user';
import { EDatasetsSorting } from '../types/dataset';

export const processesTasksSortingValues = Object.values(ETaskListSorting);
export const processesTasksCompleteSortingValues = Object.values(ETaskListCompleteSorting);
export const workflowsSortingValues = Object.values(ETemplatesSorting);
export const workflowLogSortingValues = Object.values(EWorkflowsLogSorting);
export const workflowLogAttachmentsModes = Object.values(EWorkflowLogAttachmentsModes);
export const userListSortingValues = Object.values(EUserListSorting);
export const groupListSortingValues = Object.values(EGroupsListSorting);
export const datasetsSortingValues = Object.values(EDatasetsSorting);

export const datasetsOrderingMap: Record<string, string> = {
  [EDatasetsSorting.NameAsc]: 'name',
  [EDatasetsSorting.NameDesc]: '-name',
  [EDatasetsSorting.DateAsc]: 'date',
  [EDatasetsSorting.DateDesc]: '-date',
};

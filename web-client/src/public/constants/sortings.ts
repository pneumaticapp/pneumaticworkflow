import {
  EWorkflowLogAttachmentsModes,
  EWorkflowsLogSorting,
  ETemplatesSorting,
} from '../types/workflow';
import { ETaskListCompleteSorting, ETaskListSorting } from '../types/tasks';
import { EUserListSorting } from '../types/user';

export const processesTasksSortingValues = Object.values(ETaskListSorting);
export const processesTasksCompleteSortingValues = Object.values(ETaskListCompleteSorting);
export const workflowsSortingValues = Object.values(ETemplatesSorting);
export const workflowLogSortingValues = Object.values(EWorkflowsLogSorting);
export const workflowLogAttachmentsModes = Object.values(EWorkflowLogAttachmentsModes);
export const userListSortingValues = Object.values(EUserListSorting);

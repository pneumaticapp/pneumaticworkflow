import type { IWorkflowLog } from '../types';
import type { IStoreWorkflows } from '../workflows/types';
import type { RootState } from '../store';
import type {
  EWorkflowsLoadingStatus,
  EWorkflowsStatus,
  EWorkflowsView,
  EWorkflowsSorting,
  ITemplateFilterItem,
  TUserCounter,
} from '../../types/workflow';

export const getWorkflowsStore = (state: RootState): IStoreWorkflows => state.workflows;

export const getWorkflowsSearchText = (state: RootState): string => state.workflows.workflowsSearchText;

export const getWorkflowsLoadingStatus = (state: RootState): EWorkflowsLoadingStatus =>
  state.workflows.workflowsLoadingStatus;

export const getWorkflowLog = (state: RootState): IWorkflowLog => state.workflows.workflowLog;

export const getIsTuneViewModalOpen = (state: RootState): boolean => state.workflows.WorkflowsTuneViewModal.isOpen;

export const getWorkflowsView = (state: RootState): EWorkflowsView => state.workflows.workflowsSettings.view;

export const getWorkflowStartersCounters = (state: RootState): TUserCounter[] =>
  state.workflows.workflowsSettings.counters.workflowStartersCounters;

export const getWorkflowPerformersCounters = (state: RootState): TUserCounter[] =>
  state.workflows.workflowsSettings.counters.performersCounters;

export const getSavedFields = (state: RootState): string[] => state.workflows.workflowsSettings.selectedFields;

export const getLastLoadedTemplateIdForTable = (state: RootState): string | null =>
  state.workflows.workflowsSettings.lastLoadedTemplateIdForTable;

export const getWorkflowTemplateListItems = (state: RootState): ITemplateFilterItem[] =>
  state.workflows.workflowsSettings.templateList.items;

export const getWorkflowTemplateListIsLoading = (state: RootState): boolean =>
  state.workflows.workflowsSettings.templateList.isLoading;

export const getWorkflowsStatus = (state: RootState): EWorkflowsStatus =>
  state.workflows.workflowsSettings.values.statusFilter;

export const getWorkflowsSorting = (state: RootState): EWorkflowsSorting => state.workflows.workflowsSettings.sorting;

export const getWorkflowStartersIdsFilter = (state: RootState): number[] =>
  state.workflows.workflowsSettings.values.workflowStartersIdsFilter;

export const getWorkflowTemplatesIdsFilter = (state: RootState): number[] =>
  state.workflows.workflowsSettings.values.templatesIdsFilter;

export const getWorkflowTasksApiNamesFilter = (state: RootState): string[] =>
  state.workflows.workflowsSettings.values.tasksApiNamesFilter;

export const getWorkflowPerformersGroupsIdsFilter = (state: RootState): number[] =>
  state.workflows.workflowsSettings.values.performersGroupIdsFilter;

export const getWorkflowPerformersIdsFilter = (state: RootState): number[] =>
  state.workflows.workflowsSettings.values.performersIdsFilter;

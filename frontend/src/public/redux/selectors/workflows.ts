import { IApplicationState, IStoreWorkflows, IWorkflowLog } from '../../types/redux';
import {
  EWorkflowsLoadingStatus,
  EWorkflowsStatus,
  EWorkflowsView,
  ITemplateFilterItem,
  TUserCounter,
} from '../../types/workflow';

export const getWorkflowsStore = (state: IApplicationState): IStoreWorkflows => state.workflows;

export const getWorkflowsSearchText = (state: IApplicationState): string => state.workflows.workflowsSearchText;

export const getWorkflowsLoadingStatus = (state: IApplicationState): EWorkflowsLoadingStatus =>
  state.workflows.workflowsLoadingStatus;

export const getWorkflowLog = (state: IApplicationState): IWorkflowLog => state.workflows.workflowLog;

export const getIsTuneViewModalOpen = (state: IApplicationState): boolean =>
  state.workflows.WorkflowsTuneViewModal.isOpen;

export const getWorkflowsView = (state: IApplicationState): EWorkflowsView => state.workflows.workflowsSettings.view;

export const getWorkflowStartersCounters = (state: IApplicationState): TUserCounter[] =>
  state.workflows.workflowsSettings.counters.workflowStartersCounters;

export const getWorkflowPerformersCounters = (state: IApplicationState): TUserCounter[] =>
  state.workflows.workflowsSettings.counters.performersCounters;

export const getSavedFields = (state: IApplicationState): string[] => state.workflows.workflowsSettings.selectedFields;

export const getLastLoadedTemplateIdForTable = (state: IApplicationState): string | null =>
  state.workflows.workflowsSettings.lastLoadedTemplateIdForTable;

export const getWorkflowTemplateListItems = (state: IApplicationState): ITemplateFilterItem[] =>
  state.workflows.workflowsSettings.templateList.items;

export const getWorkflowsStatus = (state: IApplicationState): EWorkflowsStatus =>
  state.workflows.workflowsSettings.values.statusFilter;

export const getWorkflowStartersIdsFilter = (state: IApplicationState): number[] =>
  state.workflows.workflowsSettings.values.workflowStartersIdsFilter;

export const getWorkflowTemplatesIdsFilter = (state: IApplicationState): number[] =>
  state.workflows.workflowsSettings.values.templatesIdsFilter;

export const getWorkflowTasksApiNamesFilter = (state: IApplicationState): string[] =>
  state.workflows.workflowsSettings.values.tasksApiNamesFilter;

export const getWorkflowPerformersGroupsIdsFilter = (state: IApplicationState): number[] =>
  state.workflows.workflowsSettings.values.performersGroupIdsFilter;

export const getWorkflowPerformersIdsFilter = (state: IApplicationState): number[] =>
  state.workflows.workflowsSettings.values.performersIdsFilter;

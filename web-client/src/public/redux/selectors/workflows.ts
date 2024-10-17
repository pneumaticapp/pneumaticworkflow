import { IApplicationState, IStoreTask, IStoreWorkflows, IWorkflowLog } from '../../types/redux';
import { EWorkflowsStatus, EWorkflowsView } from '../../types/workflow';

export const getWorkflowsSearchText = (state: IApplicationState): string => state.workflows.workflowsSearchText;

export const getWorkflowsStore = (state: IApplicationState): IStoreWorkflows => state.workflows;

export const getTaskStore = (state: IApplicationState): IStoreTask => state.task;

export const getWorkflowLog = (state: IApplicationState): IWorkflowLog => state.workflows.workflowLog;

export const getWorkflowsStatus = (state: IApplicationState): EWorkflowsStatus =>
  state.workflows.workflowsSettings.values.statusFilter;

export const getWorkflowsView = (state: IApplicationState): EWorkflowsView => state.workflows.workflowsSettings.view;

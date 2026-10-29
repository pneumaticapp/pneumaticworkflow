import { IApplicationState, IWorkflowLog } from '../../types/redux';

export const getWorkflowLogStore = (state: IApplicationState): IWorkflowLog => {
  return state.workflows.workflowLog;
};

export const getWorkflowLogIsLoading = (state: IApplicationState): boolean => state.workflows.workflowLog.isLoading;

export const getWorkflowLogWorkflowId = (state: IApplicationState): number | null =>
  state.workflows.workflowLog.workflowId;

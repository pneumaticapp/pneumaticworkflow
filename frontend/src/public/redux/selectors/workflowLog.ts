import type { IWorkflowLog } from '../types';
import type { RootState } from '../store';

export const getWorkflowLogStore = (state: RootState): IWorkflowLog => {
  return state.workflows.workflowLog;
};

export const getWorkflowLogIsLoading = (state: RootState): boolean => state.workflows.workflowLog.isLoading;

export const getWorkflowLogWorkflowId = (state: RootState): number | null => state.workflows.workflowLog.workflowId;

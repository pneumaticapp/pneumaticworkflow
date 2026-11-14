import type { IWorkflowLog } from '../types';
import type { RootState } from '../store';

export const getWorkflowLogStore = (state: RootState): IWorkflowLog => {
  return state.workflows.workflowLog;
};

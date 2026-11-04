import { IWorkflowLog } from '../../types/redux';
import type { RootState } from '../store';

export const getWorkflowLogStore = (state: RootState): IWorkflowLog => {
  return state.workflows.workflowLog;
};

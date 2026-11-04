import { IWorkflowLog } from '../../types/redux';
import type { IApplicationState } from '../store';

export const getWorkflowLogStore = (state: IApplicationState): IWorkflowLog => {
  return state.workflows.workflowLog;
};

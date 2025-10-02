import { IApplicationState, IWorkflowLog } from '../../types/redux';

export const getWorkflowLogStore = (state: IApplicationState): IWorkflowLog => {
  return state.workflows.workflowLog;
};

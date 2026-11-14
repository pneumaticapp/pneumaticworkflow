import type { ITask } from '../../types/tasks';
import type { IWorkflowDetails } from '../../types/workflow';
import type { IWorkflowLog } from '../types';

export enum ETaskCardState {
  WaitingForAction = 'waiting-for-action',
  Loading = 'loading',
  Returning = 'returning',
  Completing = 'completing',
  Completed = 'completed',
}

export interface IStoreTask {
  data: ITask | null;
  workflow: IWorkflowDetails | null;
  isWorkflowLoading: boolean;
  workflowLog: IWorkflowLog;
  status: ETaskCardState;
}

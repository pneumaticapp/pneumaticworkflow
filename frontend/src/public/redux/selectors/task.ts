import { IApplicationState, IStoreTask, IWorkflowLog } from '../../types/redux';
import { ITask } from '../../types/tasks';
import { RawPerformer } from '../../types/template';
import { ETaskStatus } from '../actions';

export const getTaskStore = (state: IApplicationState): IStoreTask => state.task;

export const getCurrentTask = (state: IApplicationState): ITask | null => state.task.data;
export const getTaskPerformers = (state: IApplicationState): RawPerformer[] => state.task.data?.performers || [];

export const getCurrentTaskWorkflowLog = (state: IApplicationState): IWorkflowLog => state.task.workflowLog;
export const getCurrentTaskStatus = (state: IApplicationState): ETaskStatus => state.task.status;

import { IStoreTask, IWorkflowLog } from '../../types/redux';
import type { RootState } from '../store';
import { ITask } from '../../types/tasks';
import { RawPerformer } from '../../types/template';
import { ETaskStatus } from '../actions';

export const getTaskStore = (state: RootState): IStoreTask => state.task;

export const getCurrentTask = (state: RootState): ITask | null => state.task.data;
export const getTaskPerformers = (state: RootState): RawPerformer[] => state.task.data?.performers || [];

export const getCurrentTaskWorkflowLog = (state: RootState): IWorkflowLog => state.task.workflowLog;
export const getCurrentTaskStatus = (state: RootState): ETaskStatus => state.task.status;

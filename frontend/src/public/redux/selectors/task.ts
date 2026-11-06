import type { ETaskCardState, IStoreTask } from '../task/types';
import type { IWorkflowLog } from '../types';
import type { RootState } from '../store';
import type { ITask } from '../../types/tasks';
import type { RawPerformer } from '../../types/template';

export const getTaskStore = (state: RootState): IStoreTask => state.task;

export const getCurrentTask = (state: RootState): ITask | null => state.task.data;
export const getTaskPerformers = (state: RootState): RawPerformer[] => state.task.data?.performers || [];

export const getCurrentTaskWorkflowLog = (state: RootState): IWorkflowLog => state.task.workflowLog;
export const getCurrentTaskStatus = (state: RootState): ETaskCardState => state.task.status;

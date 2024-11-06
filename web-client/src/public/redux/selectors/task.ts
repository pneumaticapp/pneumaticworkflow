import { IApplicationState } from '../../types/redux';
import { ITask } from '../../types/tasks';
import { ETaskStatus } from '../actions';

export const getCurrentTask = (state: IApplicationState): ITask | null => state.task.data;
export const getCurrentTaskStatus = (state: IApplicationState): ETaskStatus => state.task.status;
export const getTaskPerformers = (state: IApplicationState): number[] => state.task.data?.performers || [];

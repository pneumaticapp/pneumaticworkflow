import { IWorkflowTaskClient } from '../../../types/workflow';
import { getPercent } from '../../../utils/helpers';

export interface IGetgWorkflowProgressConfig {
  completedTasks: IWorkflowTaskClient[];
  tasksCountWithoutSkipped: number;
}

export function getWorkflowProgress({ completedTasks, tasksCountWithoutSkipped }: IGetgWorkflowProgressConfig) {
  return getPercent(completedTasks.length, tasksCountWithoutSkipped);
}

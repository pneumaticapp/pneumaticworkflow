import { EWorkflowStatus } from '../../../types/workflow';
import { getPercent } from '../../../utils/helpers';
import { countCompletedTasks } from './countCompletedTasks';

export interface IGetgWorkflowProgressConfig {
  currentTask: number;
  tasksCount: number;
  status: EWorkflowStatus;
}

export function getWorkflowProgress(config: IGetgWorkflowProgressConfig) {
  return getPercent(countCompletedTasks(config.currentTask, config.status), config.tasksCount);
}

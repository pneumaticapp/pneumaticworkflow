import { EWorkflowStatus } from '../../../types/workflow';
import { getPercent } from '../../../utils/helpers';
import { countCompletedTasks } from './countCompletedTasks';

export interface IGetgWorkflowProgressConfig {
  lastActiveCurrentTask: number;
  tasksCountWithoutSkipped: number;
  status: EWorkflowStatus;
}

export function getWorkflowProgress(config: IGetgWorkflowProgressConfig) {
  return getPercent(countCompletedTasks(config.lastActiveCurrentTask, config.status), config.tasksCountWithoutSkipped);
}

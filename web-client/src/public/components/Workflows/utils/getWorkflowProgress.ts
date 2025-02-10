import { EWorkflowStatus } from '../../../types/workflow';
import { getPercent } from '../../../utils/helpers';
import { countCompletedTasks } from './countCompletedTasks';

export interface IGetgWorkflowProgressConfig {
  activeCurrentTask: number;
  activeTasksCount: number;
  status: EWorkflowStatus;
}

export function getWorkflowProgress(config: IGetgWorkflowProgressConfig) {
  return getPercent(countCompletedTasks(config.activeCurrentTask, config.status), config.activeTasksCount);
}

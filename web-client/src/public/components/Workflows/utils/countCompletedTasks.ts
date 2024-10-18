import { EWorkflowStatus } from '../../../types/workflow';

export function countCompletedTasks(currentTask: number, processStatus: EWorkflowStatus) {
  return processStatus === EWorkflowStatus.Finished ? currentTask : currentTask - 1;
}

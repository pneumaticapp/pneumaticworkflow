import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export interface IReturnWorkflowToTaskConfig {
  id: number;
  taskId: number;
}

export function returnWorkflowToTask({id, taskId}: IReturnWorkflowToTaskConfig) {
  const { api: { urls }} = getBrowserConfigEnv();
  const url = urls.returnWorkflowToTask.replace(':id', String(id));

  return commonRequest(
    url,
    {
      body: mapRequestBody({task: taskId}),
      method: 'POST',
    },
    { responseType: 'empty', shouldThrow: true },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function addTaskAiPerformer(taskId: number, aiAgentId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.addTaskAiPerformer.replace(':id', String(taskId)),
    {
      method: 'POST',
      data: mapRequestBody({ aiAgentId }),
    },
    {
      responseType: 'empty',
      shouldThrow: true,
    },
  );
}

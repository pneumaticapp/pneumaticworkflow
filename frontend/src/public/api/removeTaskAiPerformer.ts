import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function removeTaskAiPerformer(taskId: number, aiAgentId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.removeTaskAiPerformer.replace(':id', String(taskId)),
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

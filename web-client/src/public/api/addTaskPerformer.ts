import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function addTaskPerformer(taskId: number, userId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.addTaskPerformer.replace(':id', String(taskId)),
    {
      method: 'POST',
      body: mapRequestBody({ userId }),
    },
    {
      responseType: 'empty',
      shouldThrow: true,
    },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function removeTaskPerformerGroup(taskId: number, groupId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.removeTaskPerformerGroup.replace(':id', String(taskId)),
    {
      method: 'POST',
      data: mapRequestBody({ groupId }),
    },
    {
      responseType: 'empty',
      shouldThrow: true,
    },
  );
}

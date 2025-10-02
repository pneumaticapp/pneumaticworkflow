import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function addTaskPerformerGroup(taskId: number, groupId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.addTaskPerformerGroup.replace(':id', String(taskId)),
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

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function changeTaskDueDate(taskId: number, dueDate: string) {
  const { api: { urls } } = getBrowserConfigEnv();

  const url = urls.taskDueDate.replace(':id', taskId);

  return commonRequest(url, {
    method: 'POST',
    body: mapRequestBody({ dueDate })
  }, {
    shouldThrow: true,
  });
}

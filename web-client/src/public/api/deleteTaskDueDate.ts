import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function deleteTaskDueDate(taskId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  const url = urls.taskDueDate.replace(':id', taskId);

  return commonRequest(url, {
    method: 'DELETE',
  }, {
    shouldThrow: true,
  });
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function changeTaskDueDate(taskId: number, dueDateTsp: number | null) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.taskDueDate.replace(':id', taskId);

  return commonRequest(
    url,
    {
      method: 'POST',
      data: mapRequestBody({ dueDateTsp }),
    },
    {
      shouldThrow: true,
    },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import type { ITaskAPI } from '../types/tasks';

export function getTask(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.task.replace(':id', String(id));

  return commonRequest<ITaskAPI>(url, {}, { shouldThrow: true });
}

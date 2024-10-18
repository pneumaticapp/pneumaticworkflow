import { commonRequest } from './commonRequest';

export interface IGetTasksCountResponse {
  tasksCount: number;
}

export function getTasksCount() {
  return commonRequest<IGetTasksCountResponse>('getTasksCount', {
    method: 'GET',
  });
}

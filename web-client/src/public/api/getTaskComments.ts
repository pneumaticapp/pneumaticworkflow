import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITaskCommentItem } from '../types/workflow';
import { DEFAULT_TASK_COMMENTS_LIMIT } from '../constants/defaultValues';

export interface IGetTaskCommentsResponse {
  count: number;
  next: string;
  previous: string;
  results: ITaskCommentItem[];
}

export interface IGetTaskCommentsConfig {
  id: number;
  offset: number;
  limit: number;
}

export function getTaskComments({
  id = 0,
  offset = 0,
  limit = DEFAULT_TASK_COMMENTS_LIMIT,
}: Partial<IGetTaskCommentsConfig>) {
  const { api: { urls }} = getBrowserConfigEnv();
  const baseUrl = urls.tasksComments.replace(':id', String(id));
  const query = getTaskCommentsQueryString({ limit, offset });
  const url = `${baseUrl}?${query}`;

  return commonRequest<IGetTaskCommentsResponse>(
    url,
    {},
    { shouldThrow: true },
  );
}

export function getTaskCommentsQueryString({
  limit,
  offset,
}: Pick<IGetTaskCommentsConfig, 'limit' | 'offset'>) {
  return [
    `limit=${limit}`,
    `offset=${offset}`,
  ].filter(Boolean).join('&');
}

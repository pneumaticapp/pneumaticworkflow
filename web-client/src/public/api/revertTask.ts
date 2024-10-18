import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface ISendTaskCommentResponse {
  text: string;
  process: number;
}

export interface ISendTaskCommentConfig {
  id: number;
}

export function revertTask({
  id = 0,
}: Partial<ISendTaskCommentConfig>) {
  const { api: { urls }} = getBrowserConfigEnv();

  const url = urls.revertTask.replace(':id', String(id));

  return commonRequest<ISendTaskCommentResponse>(
    url,
    {
      method: 'POST',
    }, {responseType: 'empty', shouldThrow: true},
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface ISendTaskCommentResponse {
  text: string;
  process: number;
}

export interface ISendTaskCommentConfig {
  id: number;
  comment: string;
}

export function revertTask({ id = 0, comment }: Partial<ISendTaskCommentConfig>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.revertTask.replace(':id', String(id));

  return commonRequest<ISendTaskCommentResponse>(
    url,
    {
      method: 'POST',
      data: JSON.stringify({ comment }),
    },
    { responseType: 'empty', shouldThrow: true },
  );
}

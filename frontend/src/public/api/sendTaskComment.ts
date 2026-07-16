import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export interface ISendTaskCommentResponse {
  text: string;
  process: number;
}

export interface ISendTaskCommentConfig {
  taskId: number;
  text?: string;
}

export function sendTaskComment({ taskId, text = '' }: ISendTaskCommentConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.taskComment.replace(':id', String(taskId));

  return commonRequest<ISendTaskCommentResponse>(
    url,
    {
      data: mapRequestBody({ text }),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

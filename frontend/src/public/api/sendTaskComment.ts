import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { TUploadedFile } from '../utils/uploadFiles';

export interface ISendTaskCommentResponse {
  text: string;
  process: number;
  attachments: TUploadedFile[];
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

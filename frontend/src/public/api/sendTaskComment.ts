import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { ITaskCommentAttachmentRequest } from '../types/workflow';
import { TUploadedFile } from '../utils/uploadFilesNew';

export interface ISendTaskCommentResponse {
  text: string;
  process: number;
  attachments: TUploadedFile[];
}

export interface ISendTaskCommentConfig {
  taskId: number;
  text?: string;
  attachments?: ITaskCommentAttachmentRequest[];
}

export function sendTaskComment({ taskId, text = '', attachments = [] }: ISendTaskCommentConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.taskComment.replace(':id', String(taskId));

  return commonRequest<ISendTaskCommentResponse>(
    url,
    {
      data: mapRequestBody({ text, attachments }),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

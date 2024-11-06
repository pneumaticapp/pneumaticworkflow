import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { ITaskCommentAttachmentRequest } from '../types/workflow';
import { TUploadedFile } from '../utils/uploadFiles';

export interface ISendWorkflowCommentResponse {
  text: string;
  process: number;
  attachments: TUploadedFile[];
}

export interface ISendWorkflowCommentConfig {
  id: number;
  text: string;
  attachments?: ITaskCommentAttachmentRequest[];
}

export function sendWorkflowComment({
  id = 0,
  text = '',
  attachments = [],
}: Partial<ISendWorkflowCommentConfig>) {
  const { api: { urls }} = getBrowserConfigEnv();

  const url = urls.workflowComment.replace(':id', String(id));

  return commonRequest<ISendWorkflowCommentResponse>(
    url,
    {
      body: mapRequestBody({text, attachments }),
      method: 'POST',
    },
    {shouldThrow: true},
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export interface ISendWorkflowCommentResponse {
  text: string;
  process: number;
}

export interface ISendWorkflowCommentConfig {
  id: number;
  text: string;
}

export function sendWorkflowComment({ id = 0, text = '' }: Partial<ISendWorkflowCommentConfig>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflowComment.replace(':id', String(id));

  return commonRequest<ISendWorkflowCommentResponse>(
    url,
    {
      data: mapRequestBody({ text }),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

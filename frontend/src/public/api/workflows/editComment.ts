import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import { ISendWorkflowCommentResponse } from '../sendWorkflowComment';
import { ITaskCommentAttachmentRequest } from '../../types/workflow';

export interface IEditComment {
  id: number;
  text: string | null;
  attachments: ITaskCommentAttachmentRequest[] | null;
}

export function editComment({ id, text, attachments }: IEditComment) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflowCommentEdit.replace(':id', String(id));

  return commonRequest<ISendWorkflowCommentResponse>(
    url,
    {
      method: 'PATCH',
      data: mapRequestBody({
        text,
        attachments,
      }),
    },
    { shouldThrow: true },
  );
}

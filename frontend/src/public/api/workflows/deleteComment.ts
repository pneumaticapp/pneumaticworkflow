import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { ISendWorkflowCommentResponse } from '../sendWorkflowComment';

export interface IDeleteComment {
  id: number;
}

export function deleteComment({ id }: IDeleteComment) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflowCommentDelete.replace(':id', String(id));

  return commonRequest<ISendWorkflowCommentResponse>(
    url,
    {
      method: 'DELETE',
    },
    { shouldThrow: true },
  );
}

import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export interface IDeleteReaction {
  id: number;
  value: string;
}

export function deleteReactionComment({ id, value }: IDeleteReaction) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflowCommentDeleteReaction.replace(':id', String(id));

  return commonRequest(
    url,
    {
      method: 'POST',
      body: mapRequestBody({
        value,
      }),
    },
    { responseType: 'empty', shouldThrow: true },
  );
}

import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export interface ICreateReaction {
  id: number;
  value: string;
}

export function createReactionComment({ id, value }: ICreateReaction) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflowCommentCreateReaction.replace(':id', String(id));

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

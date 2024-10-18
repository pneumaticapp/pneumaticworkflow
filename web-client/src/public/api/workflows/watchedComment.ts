import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export interface IWatchedComment {
  id: number;
}

export function watchedComment({ id }: IWatchedComment) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflowCommentWatched.replace(':id', String(id));

  return commonRequest(
    url,
    {
      method: 'POST',
    },
    { responseType: 'empty', shouldThrow: true },
  );
}

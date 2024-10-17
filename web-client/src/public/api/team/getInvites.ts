import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

import { IUserInvite } from '../../types/team';

export function getInvites() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IUserInvite[]>(urls.getInvites);
}

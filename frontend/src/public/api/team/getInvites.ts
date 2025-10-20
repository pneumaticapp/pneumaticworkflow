import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { UserInvite } from '../../types/team';

export function getInvites() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<UserInvite[]>(urls.getInvites);
}

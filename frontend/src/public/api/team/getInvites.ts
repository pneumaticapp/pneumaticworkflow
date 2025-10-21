import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { UserInvite } from '../../redux/team/types';

export function getInvites() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<UserInvite[]>(urls.getInvites);
}

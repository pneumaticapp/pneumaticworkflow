import { getBrowserConfigEnv } from '../utils/getConfig';
import { commonRequest } from './commonRequest';

export interface IGetActiveUsersCountResponse {
  activeUsers: number;
  tenantsActiveUsers: number;
}

export function getActiveUsersCount() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IGetActiveUsersCountResponse>(urls.getActiveUsersCount);
}

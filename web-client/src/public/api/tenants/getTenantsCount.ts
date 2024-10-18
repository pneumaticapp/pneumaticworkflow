import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export interface IGetTenantsCountResponse {
  count: number;
}

export function getTenantsCount() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IGetTenantsCountResponse>(urls.tenantsCount);
}

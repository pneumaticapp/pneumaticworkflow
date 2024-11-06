import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export interface IGetTenantTokenResponse {
  token: string;
}

export function getTenantToken(accountId: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.tenantToken.replace(':id', accountId);

  return commonRequest<IGetTenantTokenResponse>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}

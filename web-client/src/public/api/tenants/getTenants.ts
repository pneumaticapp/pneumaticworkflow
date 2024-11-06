import { commonRequest } from '../commonRequest';
import { ETenantsSorting, ITenant } from '../../types/tenants';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export interface IGetTenantsConfig {
  sorting: ETenantsSorting;
}

export function getTenants(config: IGetTenantsConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = `${urls.tenants}?${getTenantsQueryString(config)}`;

  return commonRequest<ITenant[]>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}

export function getTenantsQueryString({ sorting }: IGetTenantsConfig) {
  const QS_BY_SORTING: { [key in ETenantsSorting]: string } = {
    [ETenantsSorting.NameAsc]: 'ordering=tenant_name',
    [ETenantsSorting.NameDesc]: 'ordering=-tenant_name',
    [ETenantsSorting.DateAsc]: 'ordering=date_joined',
    [ETenantsSorting.DateDesc]: 'ordering=-date_joined',
  };

  return [QS_BY_SORTING[sorting]].filter(Boolean).join('&');
}

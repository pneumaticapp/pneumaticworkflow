import { commonRequest } from '../commonRequest';
import { ITenant } from '../../types/tenants';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export interface ICreateTenantConfig {
  name: string;
}

export function createTenant({ name }: ICreateTenantConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.createTenant;

  return commonRequest<ITenant[]>(
    url,
    {
      method: 'POST',
      body: mapRequestBody({
        tenant_name: name,
      }),
    },
    {
      shouldThrow: true,
    },
  );
}

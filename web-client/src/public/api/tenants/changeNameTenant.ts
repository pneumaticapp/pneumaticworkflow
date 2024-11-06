import { commonRequest } from '../commonRequest';
import { ITenant } from '../../types/tenants';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export interface IDeleteTenantConfig {
  id: number;
  name: String;
}

export function changeNameTenant({ id, name }: IDeleteTenantConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.changeNameTenant.replace(':id', String(id));

  return commonRequest<ITenant[]>(
    url,
    {
      method: 'PATCH',
      body: mapRequestBody({
        tenant_name: name,
      }),
    },
    {
      shouldThrow: true,
    },
  );
}

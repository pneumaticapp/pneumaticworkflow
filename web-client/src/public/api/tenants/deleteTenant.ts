import { commonRequest } from '../commonRequest';
import { ITenant } from '../../types/tenants';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export interface IDeleteTenantConfig {
  id: number;
}

export function deleteTenant({ id }: IDeleteTenantConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.deleteTenant.replace(':id', String(id));

  return commonRequest<ITenant[]>(
    url,
    {
      method: 'DELETE',
    },
    { shouldThrow: true, responseType: 'empty' },
  );
}

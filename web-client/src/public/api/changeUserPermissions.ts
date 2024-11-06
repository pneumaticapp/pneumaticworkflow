import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function changeUserPermissions(id: number) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest(
    urls.changeUserPermissions.replace(':id', String(id)),
    {method: 'POST'},
    {responseType: 'empty', shouldThrow: true},
  );
}

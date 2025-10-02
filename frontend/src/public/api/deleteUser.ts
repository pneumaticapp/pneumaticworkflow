import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function deleteUser(id: number) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest(
    urls.deleteUser.replace(':id', String(id)),
    {method: 'POST'},
    {type: 'local', shouldThrow: true, responseType: 'empty'},
  );
}

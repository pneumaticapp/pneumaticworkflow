import { getBrowserConfigEnv } from '../utils/getConfig';
import { commonRequest } from './commonRequest';

export function sendSignOut() {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest(urls.signOut, {
    method: 'POST',
  }, {
    type: 'local',
    responseType: 'empty',
    shouldThrow: false,
  });
}

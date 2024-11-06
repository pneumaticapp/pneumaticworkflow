import { commonRequest } from './commonRequest';
import { getBrowserConfig } from '../utils/getConfig';

export function verificateAccount(token: string) {
  const { config: { api: { urls } } } = getBrowserConfig();

  return commonRequest(`${urls.verificateAccount}?token=${token}`, {
    headers: {
      'Content-Type': 'text/plain',
    },
  }, {
    shouldThrow: true,
    responseType: 'empty',
    type: 'local',
  });
}

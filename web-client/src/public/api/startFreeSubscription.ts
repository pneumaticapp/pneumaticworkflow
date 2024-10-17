import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function startFreeSubscription() {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest(
    urls.startFreeSubscription,
    {
      method: 'POST',
    },
    { shouldThrow: true, responseType: 'empty' },
  );
}

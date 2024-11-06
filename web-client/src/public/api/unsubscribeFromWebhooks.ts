import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EWebhooksTypeEvent } from '../types/webhooks';

export function unsubscribeFromWebhooks(event: EWebhooksTypeEvent) {
  const { api: { urls }} = getBrowserConfigEnv();

  const URL = urls.webhooksUnsubscribe.replace(':event', String(event));

  return commonRequest(
    URL,
    { method: 'POST' },
    {
      shouldThrow: true,
      responseType: 'empty',
    },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { EWebhooksTypeEvent } from '../types/webhooks';

export function subscribeToWebhooks(event: EWebhooksTypeEvent, url: string) {
  const { api: { urls }} = getBrowserConfigEnv();

  const URL = urls.webhooksSubscribe.replace(':event', String(event));

  return commonRequest(
    URL,
    {
      method: 'POST',
      body: mapRequestBody({ url }),
    },
    {
      shouldThrow: true,
      responseType: 'empty',
    },
  );
}

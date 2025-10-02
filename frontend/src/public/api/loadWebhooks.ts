import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EWebhooksTypeEvent, IWebhookUrl } from '../types/webhooks';

export type TLoadWebhooksResponse = {
  event: EWebhooksTypeEvent;
  url: IWebhookUrl;
};

export function loadWebhooks() {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest<TLoadWebhooksResponse[]>(
    urls.webhooks,
    { method: 'GET' },
    { shouldThrow: true },
  );
}

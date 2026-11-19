import type { EWebhooksTypeEvent, IWebhook } from '../../types/webhooks';

export type TWebhookStore = Record<EWebhooksTypeEvent, IWebhook>;

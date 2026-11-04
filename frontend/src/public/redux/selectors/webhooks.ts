import type { IApplicationState } from '../store';

export const getWebhooks = (state: IApplicationState) => state.webhooks;

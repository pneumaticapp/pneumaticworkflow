import type { RootState } from '../store';

export const getWebhooks = (state: RootState) => state.webhooks;

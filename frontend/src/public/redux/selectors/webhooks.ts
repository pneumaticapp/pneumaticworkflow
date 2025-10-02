import { IApplicationState } from '../../types/redux';

export const getWebhooks = (state: IApplicationState) => state.webhooks;

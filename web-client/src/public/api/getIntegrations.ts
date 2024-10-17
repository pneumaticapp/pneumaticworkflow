import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IIntegrationListItem } from '../types/integrations';

export type TGetIntegrationsResponse = IIntegrationListItem[];

export function getIntegrations() {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TGetIntegrationsResponse>(
    urls.integrations,
    {},
    { shouldThrow: true },
  );
}

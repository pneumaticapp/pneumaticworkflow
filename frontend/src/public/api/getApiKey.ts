import { IApiKeyCreateResponse, IApiKeyItem } from '../types/integrations';
import { commonRequest } from './commonRequest';

export function getApiKeys() {
  return commonRequest<IApiKeyItem[]>(
    'apiKeys',
    {},
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}

export function createApiKey(name?: string) {
  return commonRequest<IApiKeyCreateResponse>(
    'apiKeys',
    { body: { name: name || '' } },
    {
      type: 'local',
      method: 'POST',
      shouldThrow: true,
    },
  );
}

export function deleteApiKey(id: number) {
  return commonRequest<void>(
    'apiKeys',
    { urlParams: { id } },
    {
      type: 'local',
      method: 'DELETE',
      shouldThrow: true,
    },
  );
}

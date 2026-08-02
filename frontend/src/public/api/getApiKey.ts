import { IApiKeyCreateResponse, IApiKeyItem } from '../types/integrations';
import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function getApiKeys() {
  const { api: { urls } } = getBrowserConfigEnv();
  const url = urls.apiKeys.replace('/:id?', '');

  return commonRequest<IApiKeyItem[]>(
    url,
    {},
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}

export function createApiKey(name: string) {
  const { api: { urls } } = getBrowserConfigEnv();
  const url = urls.apiKeys.replace('/:id?', '');

  return commonRequest<IApiKeyCreateResponse>(
    url,
    {
      method: 'POST',
      data: { name },
    },
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}

export function deleteApiKey(id: number) {
  const { api: { urls } } = getBrowserConfigEnv();
  const url = urls.apiKeys.replace(':id?', String(id));

  return commonRequest<void>(
    url,
    {
      method: 'DELETE',
    },
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}

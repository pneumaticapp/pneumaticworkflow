import { commonRequest } from './commonRequest';

export interface IGetApiKeyResponse {
  token: string;
}

export function getApiKey() {
  return commonRequest<IGetApiKeyResponse>(
    'apiKey',
    {},
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}

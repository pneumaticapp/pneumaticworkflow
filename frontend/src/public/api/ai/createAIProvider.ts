import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import type { IAIProvider, ICreateAIProviderRequest } from './types';

export function createAIProvider(data: ICreateAIProviderRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIProvider>(
    urls.createAIProvider,
    {
      data: mapRequestBody(data),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

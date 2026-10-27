import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import type { IAIModel } from './types';

export function getAIProviderModels(providerId: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIModel[]>(
    urls.getAIProviderModels.replace(':id', String(providerId)),
    {},
    { shouldThrow: true },
  );
}

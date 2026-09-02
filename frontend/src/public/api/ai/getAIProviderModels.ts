import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAIModel } from '../../types/ai';

export function getAIProviderModels(providerId: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIModel[]>(
    urls.aiProviderModels.replace(':id', String(providerId)),
    {},
    { shouldThrow: true },
  );
}

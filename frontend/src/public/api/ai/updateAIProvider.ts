import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import { IAIProvider, TUpdateAIProviderRequest } from '../../types/ai';

export function updateAIProvider(id: number, data: TUpdateAIProviderRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIProvider>(
    urls.aiProvider.replace(':id', String(id)),
    {
      data: mapRequestBody(data),
      method: 'PATCH',
    },
    { shouldThrow: true },
  );
}

import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import { IAIProvider, ICreateAIProviderByVendorRequest } from '../../types/ai';

export function createAIProviderByVendor(data: ICreateAIProviderByVendorRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIProvider>(
    urls.createAIProviderByVendor,
    {
      data: mapRequestBody(data),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

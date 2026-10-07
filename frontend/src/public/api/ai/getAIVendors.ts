import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAIVendor } from '../../types/ai';

export function getAIVendors() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIVendor[]>(urls.getAIVendors, {}, { shouldThrow: true });
}

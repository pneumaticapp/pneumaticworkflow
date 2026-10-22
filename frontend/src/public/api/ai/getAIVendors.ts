import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import type { IAIVendor } from './types';

export function getAIVendors() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIVendor[]>(urls.getAIVendors, {}, { shouldThrow: true });
}

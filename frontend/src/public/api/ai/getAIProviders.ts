import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import type { IAIProvider } from './types';

// Returned unpaginated: the endpoint wraps the list in {count, results} only when a `limit` is passed.
export function getAIProviders() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIProvider[]>(urls.getAIProviders, {}, { shouldThrow: true });
}

import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAIProvider } from '../../types/ai';

// Returned unpaginated: the endpoint wraps the list in {count, results} only when a `limit` is passed.
export function getAIProviders() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIProvider[]>(urls.aiProviders, {}, { shouldThrow: true });
}

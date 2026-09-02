import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAIProvider } from '../../types/ai';

/**
 * Returned unpaginated: the endpoint only wraps the list in {count, results} when a `limit` is
 * passed, and the whole list is needed at once — to gate "Create AI Agent" and to read `usage`.
 */
export function getAIProviders() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIProvider[]>(urls.aiProviders, {}, { shouldThrow: true });
}

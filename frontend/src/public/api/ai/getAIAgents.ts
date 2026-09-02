import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAIAgent } from '../../types/ai';

/** Returned unpaginated — see the note in getAIProviders. */
export function getAIAgents() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIAgent[]>(urls.aiAgents, {}, { shouldThrow: true });
}

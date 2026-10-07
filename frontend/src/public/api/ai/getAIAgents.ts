import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAIAgent } from '../../types/ai';

export function getAIAgents() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIAgent[]>(urls.aiAgents, {}, { shouldThrow: true });
}

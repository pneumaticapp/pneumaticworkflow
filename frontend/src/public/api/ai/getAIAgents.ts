import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import type { IAIAgent } from './types';

export function getAIAgents() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIAgent[]>(urls.getAIAgents, {}, { shouldThrow: true });
}

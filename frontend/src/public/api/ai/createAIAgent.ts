import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import type { IAIAgent, ICreateAIAgentRequest } from './types';

export function createAIAgent(data: ICreateAIAgentRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIAgent>(
    urls.createAIAgent,
    {
      data: mapRequestBody(data),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

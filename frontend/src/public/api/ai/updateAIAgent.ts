import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import type { IAIAgent, TUpdateAIAgentRequest } from './types';

export function updateAIAgent(id: number, data: TUpdateAIAgentRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIAgent>(
    urls.updateAIAgent.replace(':id', String(id)),
    {
      data: mapRequestBody(data),
      method: 'PATCH',
    },
    { shouldThrow: true },
  );
}

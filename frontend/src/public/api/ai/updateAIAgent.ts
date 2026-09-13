import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';
import { IAIAgent, TUpdateAIAgentRequest } from '../../types/ai';

export function updateAIAgent(id: number, data: TUpdateAIAgentRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAIAgent>(
    urls.aiAgent.replace(':id', String(id)),
    {
      data: mapRequestBody(data),
      method: 'PATCH',
    },
    { shouldThrow: true },
  );
}

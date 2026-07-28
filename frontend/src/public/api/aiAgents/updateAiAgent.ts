import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAiAgent, TAiAgentDraft } from '../../redux/aiAgents/types';
import { mapRequestBody } from '../../utils/mappers';

export function updateAiAgent(id: number, agent: Partial<TAiAgentDraft>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.aiAgent.replace(':id', String(id));

  return commonRequest<IAiAgent>(
    url,
    {
      method: 'PATCH',
      data: mapRequestBody(agent),
    },
    { shouldThrow: true },
  );
}

import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IAiAgent, TAiAgentDraft } from '../../redux/aiAgents/types';
import { mapRequestBody } from '../../utils/mappers';

export function createAiAgent(agent: TAiAgentDraft) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAiAgent>(
    urls.aiAgents,
    {
      method: 'POST',
      data: mapRequestBody(agent),
    },
    { shouldThrow: true },
  );
}

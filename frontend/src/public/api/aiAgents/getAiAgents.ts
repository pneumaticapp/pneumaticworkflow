import { commonRequest } from '../commonRequest';
import { IAiAgent } from '../../redux/aiAgents/types';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getAiAgents() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAiAgent[]>(
    urls.aiAgents,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}

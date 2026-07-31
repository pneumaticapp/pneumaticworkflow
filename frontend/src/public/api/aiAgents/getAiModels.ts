import { commonRequest } from '../commonRequest';
import { IAiModel } from '../../redux/aiAgents/types';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getAiModels() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IAiModel[]>(
    urls.aiModels,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}

import { commonRequest } from '../commonRequest';
import { IAiConnection } from '../../redux/aiAgents/types';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export interface IGetAiConnectionResponse {
  connection: IAiConnection | null;
}

export function getAiConnection() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IGetAiConnectionResponse>(
    urls.aiConnection,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}

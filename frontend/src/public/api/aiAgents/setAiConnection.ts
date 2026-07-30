import { commonRequest } from '../commonRequest';
import { IAiConnection, TAiConnectionDraft } from '../../redux/aiAgents/types';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export interface ISetAiConnectionResponse {
  connection: IAiConnection;
}

export function setAiConnection(draft: TAiConnectionDraft) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<ISetAiConnectionResponse>(
    urls.aiConnection,
    {
      method: 'PUT',
      data: mapRequestBody(draft),
    },
    { shouldThrow: true },
  );
}

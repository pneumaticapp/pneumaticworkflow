import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function deleteAiAgent(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.aiAgent.replace(':id', String(id));

  return commonRequest<void>(
    url,
    {
      method: 'DELETE',
    },
    { shouldThrow: true },
  );
}

import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function deleteAIAgent(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<void>(
    urls.aiAgent.replace(':id', String(id)),
    { method: 'DELETE' },
    { shouldThrow: true },
  );
}

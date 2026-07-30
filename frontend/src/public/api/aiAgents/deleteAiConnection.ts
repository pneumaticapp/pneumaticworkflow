import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function deleteAiConnection() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<void>(
    urls.aiConnection,
    {
      method: 'DELETE',
    },
    { shouldThrow: true },
  );
}

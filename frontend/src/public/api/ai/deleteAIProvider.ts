import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function deleteAIProvider(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<void>(
    urls.aiProvider.replace(':id', String(id)),
    { method: 'DELETE' },
    { shouldThrow: true },
  );
}

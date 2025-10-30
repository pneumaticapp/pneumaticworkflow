import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function deleteWorkflow(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest(
    urls.workflow.replace(':id', String(id)),
    { method: 'DELETE' },
    { shouldThrow: true, responseType: 'empty' },
  );
}

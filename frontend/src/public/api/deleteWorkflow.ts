import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function deleteWorkflow(id: number) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest(
    urls.deleteWorkflow.replace(':id', String(id)),
    { method: 'POST' },
    { shouldThrow: true, responseType: 'empty' },
  );
}

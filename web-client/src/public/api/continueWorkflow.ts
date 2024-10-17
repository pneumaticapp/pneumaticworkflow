import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function continueWorkflow(id: number) {
  const { api: { urls }} = getBrowserConfigEnv();
  const url = urls.continueWorkflow.replace(':id', String(id));

  return commonRequest(
    url,
    {
      method: 'POST',
    },
    {
      responseType: 'empty',
      shouldThrow: true,
    },
  );
}

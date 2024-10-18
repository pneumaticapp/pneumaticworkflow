import { getBrowserConfigEnv } from '../utils/getConfig';

import { commonRequest } from './commonRequest';

export interface IFinishWorkflowConfig {
  id: number;
}

export function finishWorkflow({
  id = 0,
}: Partial<IFinishWorkflowConfig>) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest(
    urls.finishWorkflow.replace(':id', String(id)),
    {
      method: 'POST',
    },
    {
      responseType: 'empty', shouldThrow: true,
    },
  );
}

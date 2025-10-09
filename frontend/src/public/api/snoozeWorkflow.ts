import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { IWorkflowDetails } from '../types/workflow';

export function snoozeWorkflow(workflowId: number, date: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.snoozeWorkflow.replace(':id', String(workflowId));

  return commonRequest<IWorkflowDetails>(
    url,
    {
      method: 'POST',
      data: mapRequestBody({ date }),
    },
    {
      shouldThrow: true,
    },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IWorkflowDetails } from '../types/workflow';

export function getWorkflow(workflowId: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.workflow.replace(':id', String(workflowId));

  return commonRequest<IWorkflowDetails>(url, {}, { shouldThrow: true });
}

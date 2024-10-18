import { commonRequest } from './commonRequest';
import { mapRequestBody, getNormalizedKickoff } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { TEditWorkflowPayload } from '../redux/workflows/actions';
import { IWorkflowDetails } from '../types/workflow';

export interface IEditWorkflowResponse extends IWorkflowDetails {}

export function editWorkflow({ name, kickoff, workflowId, isUrgent, dueDate }: TEditWorkflowPayload) {
  const { api: { urls }} = getBrowserConfigEnv();
  const url = urls.workflow.replace(':id', String(workflowId));

  const newProcess = {
    ...(name && { name }),
    ...(kickoff && { kickoff: getNormalizedKickoff(kickoff) }),
    ...(typeof isUrgent !== 'undefined' && { isUrgent }),
    ...(typeof dueDate !== 'undefined' && { dueDate }),
  };

  return commonRequest<IEditWorkflowResponse>(url,
    {
      method: 'PATCH',
      body: mapRequestBody(newProcess, 'default', {
        ignorePropertyMapToSnakeCase: ['kickoff']
      }),
    },
    {
      shouldThrow: true,
    },
  );
}

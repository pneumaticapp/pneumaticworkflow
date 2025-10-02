import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IStartWorkflowPayload } from '../redux/workflows/actions';
import { TWorkflowDetailsResponse } from '../types/workflow';

export type TRunProcessResponse = Pick<TWorkflowDetailsResponse, 'name' | 'tasks' | 'status'>;

export function runProcess(data: IStartWorkflowPayload) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.runTemplate.replace(':id', String(data.id));

  return commonRequest<TRunProcessResponse>(
    url,
    {
      method: 'POST',
      data: mapRequestBody(data, 'default', {
        ignorePropertyMapToSnakeCase: ['kickoff'],
      }),
    },
    {
      shouldThrow: true,
    },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export type TReassignWorkflowsRequest = {
  oldUser: number;
  newUser: number;
};

export function reassignWorkflows(oldUser: number, newUser: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  const requestBody: TReassignWorkflowsRequest = { oldUser, newUser };

  return commonRequest(
    urls.reassignWorkflows,
    {
      body: mapRequestBody(requestBody),
      method: 'POST',
    },
    {
      shouldThrow: true,
      responseType: 'empty',
    },
  );
}

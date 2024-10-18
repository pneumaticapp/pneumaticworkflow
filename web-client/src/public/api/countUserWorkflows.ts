import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export type TCountUserWorkflowsResponse = {
  count: number;
};

export function countUserWorkflows(userId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TCountUserWorkflowsResponse>(
    urls.countUserWorkflows.replace(':id', String(userId)),
    {},
    { shouldThrow: true },
  );
}

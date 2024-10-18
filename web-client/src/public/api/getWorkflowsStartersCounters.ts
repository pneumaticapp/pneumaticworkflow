import { commonRequest } from './commonRequest';
import { EWorkflowsStatus, TUserCounter } from '../types/workflow';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { canFilterByCurrentPerformer } from '../utils/workflows/filters';

export interface IGetWorkflowsStartersCountersConfig {
  statusFilter: EWorkflowsStatus;
  templatesIdsFilter: number[];
  performersIdsFilter: number[];
}

export function getWorkflowsStartersCounters({
  statusFilter = EWorkflowsStatus.Running,
  templatesIdsFilter,
  performersIdsFilter,
}: IGetWorkflowsStartersCountersConfig) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TUserCounter[]>(
    `${urls.workflowsStartersCounters}?${getQueryString({
      statusFilter,
      templatesIdsFilter,
      performersIdsFilter,
    })}`,
  );
}

export function getQueryString({
  statusFilter,
  templatesIdsFilter,
  performersIdsFilter,
}: IGetWorkflowsStartersCountersConfig) {
  return [
    statusFilter !== EWorkflowsStatus.All && `status=${statusFilter}`,
    `template_ids=${templatesIdsFilter.join(',')}`,
    canFilterByCurrentPerformer(statusFilter) && `current_performer_ids=${performersIdsFilter.join(',')}`,
  ].filter(Boolean).join('&');
}

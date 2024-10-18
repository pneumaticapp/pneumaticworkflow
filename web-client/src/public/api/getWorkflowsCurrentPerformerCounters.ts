import { commonRequest } from './commonRequest';
import { EWorkflowsStatus, TUserCounter } from '../types/workflow';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EXTERNAL_USER_ID } from '../utils/users';

export interface IGetWorkflowsCurrentPerformerCountersConfig {
  statusFilter: EWorkflowsStatus;
  templatesIdsFilter: number[];
  stepsIdsFilter: number[];
  workflowStartersIdsFilter: number[];
}

export function getWorkflowsCurrentPerformerCounters({
  statusFilter = EWorkflowsStatus.Running,
  templatesIdsFilter,
  stepsIdsFilter,
  workflowStartersIdsFilter,
}: IGetWorkflowsCurrentPerformerCountersConfig) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TUserCounter[]>(
    `${urls.workflowsCurrentPerformerCounters}?${getQueryString({
      statusFilter,
      templatesIdsFilter,
      stepsIdsFilter,
      workflowStartersIdsFilter,
    })}`,
  );
}

export function getQueryString({
  statusFilter,
  templatesIdsFilter,
  stepsIdsFilter,
  workflowStartersIdsFilter,
}: IGetWorkflowsCurrentPerformerCountersConfig) {
  const isExternal = workflowStartersIdsFilter?.some(userId => userId === EXTERNAL_USER_ID);
  const workflowStarters = workflowStartersIdsFilter?.filter(userId => userId !== EXTERNAL_USER_ID);

  return [
    statusFilter !== EWorkflowsStatus.All && `status=${statusFilter}`,
    `template_ids=${templatesIdsFilter.join(',')}`,
    `template_task_ids=${stepsIdsFilter.join(',')}`,
    `workflow_starter_ids=${workflowStarters.join(',')}`,
    isExternal && 'is_external=true',
  ].filter(Boolean).join('&');
}

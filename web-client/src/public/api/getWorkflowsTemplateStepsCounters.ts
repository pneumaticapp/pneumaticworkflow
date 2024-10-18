import { commonRequest } from './commonRequest';
import { EWorkflowsStatus, TTemplateStepCounter } from '../types/workflow';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EXTERNAL_USER_ID } from '../utils/users';

export interface IGetWorkflowsTemplateStepsCountersConfig {
  statusFilter: EWorkflowsStatus;
  templatesIdsFilter: number[];
  performersIdsFilter: number[];
  workflowStartersIdsFilter: number[];
}

export function getWorkflowsTemplateStepsCounters({
  statusFilter = EWorkflowsStatus.Running,
  templatesIdsFilter,
  performersIdsFilter,
  workflowStartersIdsFilter,
}: IGetWorkflowsTemplateStepsCountersConfig) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TTemplateStepCounter[]>(
    `${urls.workflowsTemplateStepCounters}?${getQueryString({
      statusFilter,
      templatesIdsFilter,
      performersIdsFilter,
      workflowStartersIdsFilter,
    })}`,
  );
}

export function getQueryString({
  statusFilter,
  templatesIdsFilter,
  performersIdsFilter,
  workflowStartersIdsFilter,
}: IGetWorkflowsTemplateStepsCountersConfig) {
  const isExternal = workflowStartersIdsFilter?.some(userId => userId === EXTERNAL_USER_ID);
  const workflowStarters = workflowStartersIdsFilter?.filter(userId => userId !== EXTERNAL_USER_ID);

  return [
    statusFilter !== EWorkflowsStatus.All &&  `status=${statusFilter}`,
    `template_ids=${templatesIdsFilter.join(',')}`,
    statusFilter === EWorkflowsStatus.Running && `current_performer_ids=${performersIdsFilter.join(',')}`,
    `workflow_starter_ids=${workflowStarters.join(',')}`,
    isExternal && 'is_external=true',
  ].filter(Boolean).join('&');
}

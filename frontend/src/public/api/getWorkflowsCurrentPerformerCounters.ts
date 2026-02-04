import { commonRequest } from './commonRequest';
import { TUserCounter } from '../types/workflow';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EXTERNAL_USER_ID } from '../utils/users';

export interface IGetWorkflowsCurrentPerformerCountersConfig {
  templatesIdsFilter: number[];
  tasksApiNamesFilter: string[];
  workflowStartersIdsFilter: number[];
}

export function getWorkflowsCurrentPerformerCounters({
  templatesIdsFilter,
  tasksApiNamesFilter,
  workflowStartersIdsFilter,
}: IGetWorkflowsCurrentPerformerCountersConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<TUserCounter[]>(
    `${urls.workflowsCurrentPerformerCounters}?${getQueryString({
      templatesIdsFilter,
      tasksApiNamesFilter,
      workflowStartersIdsFilter,
    })}`,
  );
}

export function getQueryString({
  templatesIdsFilter,
  tasksApiNamesFilter,
  workflowStartersIdsFilter,
}: IGetWorkflowsCurrentPerformerCountersConfig) {
  const isExternal = workflowStartersIdsFilter?.some((userId) => userId === EXTERNAL_USER_ID);
  const workflowStarters = workflowStartersIdsFilter?.filter((userId) => userId !== EXTERNAL_USER_ID);

  return [
    `template_ids=${templatesIdsFilter.join(',')}`,
    `template_task_api_names=${tasksApiNamesFilter.join(',')}`,
    `workflow_starter_ids=${workflowStarters.join(',')}`,
    isExternal && 'is_external=true',
  ]
    .filter(Boolean)
    .join('&');
}

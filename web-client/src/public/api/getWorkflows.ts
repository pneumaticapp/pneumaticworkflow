import { commonRequest } from './commonRequest';
import { EWorkflowsSorting, IWorkflow, EWorkflowsStatus } from '../types/workflow';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EXTERNAL_USER_ID } from '../utils/users';
import { canFilterByCurrentPerformer, canFilterByTemplateStep } from '../utils/workflows/filters';
import { ETimeouts } from '../constants/defaultValues';

export interface IGetWorkflowsResponse {
  count: number;
  next: string;
  previous: string;
  results: IWorkflow[];
}

export interface IGetWorkflowsConfig {
  statusFilter: EWorkflowsStatus;
  offset: number;
  limit?: number;
  sorting: EWorkflowsSorting;
  templatesIdsFilter: number[];
  stepsIdsFilter: number[];
  performersIdsFilter: number[];
  workflowStartersIdsFilter: number[];
  searchText: string;
}

export function getWorkflows({
  statusFilter = EWorkflowsStatus.Running,
  offset = 0,
  sorting,
  limit = 30,
  templatesIdsFilter,
  stepsIdsFilter,
  performersIdsFilter,
  workflowStartersIdsFilter,
  searchText = '',
}: IGetWorkflowsConfig) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<IGetWorkflowsResponse>(
    `${urls.workflows}?${getWorkflowsQueryString({
      statusFilter,
      limit,
      offset,
      sorting,
      templatesIdsFilter,
      stepsIdsFilter,
      performersIdsFilter,
      workflowStartersIdsFilter,
      searchText,
    })}`,
    {},
    {
      timeOut: searchText ? ETimeouts.Prolonged : ETimeouts.Default,
    }
  );
}

export function getWorkflowsQueryString({
  statusFilter,
  limit,
  offset,
  sorting,
  templatesIdsFilter,
  stepsIdsFilter,
  performersIdsFilter,
  workflowStartersIdsFilter,
  searchText,
}: IGetWorkflowsConfig) {
  const sortingMap: { [key in EWorkflowsSorting]: string } = {
    [EWorkflowsSorting.DateAsc]: 'ordering=date',
    [EWorkflowsSorting.DateDesc]: 'ordering=-date',
    [EWorkflowsSorting.Overdue]: 'ordering=overdue',
    [EWorkflowsSorting.Urgent]: 'ordering=-urgent',
  };

  const sortingQuery = sortingMap[sorting!];

  const isExternal = workflowStartersIdsFilter?.some(userId => userId === EXTERNAL_USER_ID);
  const workflowStarters = workflowStartersIdsFilter?.filter(userId => userId !== EXTERNAL_USER_ID);

  return [
    `limit=${limit}`,
    `offset=${offset}`,
    `template_id=${templatesIdsFilter.join(',')}`,
    canFilterByTemplateStep(statusFilter) && `template_task_id=${stepsIdsFilter.join(',')}`,
    canFilterByCurrentPerformer(statusFilter) && `current_performer=${performersIdsFilter.join(',')}`,
    `workflow_starter=${workflowStarters.join(',')}`,
    statusFilter !== EWorkflowsStatus.All && `status=${statusFilter}`,
    `search=${searchText}`,
    sortingQuery,
    isExternal && 'is_external=true',
  ].filter(Boolean).join('&');
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import {
  ITask,
  ETaskListSorting,
  ETaskListCompletionStatus,
  ETaskListCompleteSorting,
} from '../types/tasks';
import { ETimeouts } from '../constants/defaultValues';

export interface IGetTasksResponse {
  count: number;
  next: string;
  previous: string;
  results: ITask[];
}

export interface IGetTasksConfig {
  id: number;
  offset: number;
  limit: number;
  sorting: ETaskListSorting | ETaskListCompleteSorting;
  templateId: number | null;
  templateStepId: number | null;
  status: ETaskListCompletionStatus;
  searchText: string;
}

const QS_BY_SORTING: {[key in ETaskListSorting]: string} = {
  [ETaskListSorting.DateAsc]: 'ordering=date',
  [ETaskListSorting.DateDesc]: 'ordering=-date',
  [ETaskListSorting.Overdue]: 'ordering=overdue',
};

const QS_BY_SORTING_COMPLETE: {[key in ETaskListCompleteSorting]: string} = {
  [ETaskListCompleteSorting.DateAsc]: 'ordering=completed',
  [ETaskListCompleteSorting.DateDesc]: 'ordering=-completed',
};

export function getUserTasks({
  id = 0,
  offset = 0,
  sorting = ETaskListSorting.DateAsc,
  templateId = null,
  templateStepId = null,
  limit = 20,
  status = ETaskListCompletionStatus.Active,
  searchText = '',
}: Partial<IGetTasksConfig>) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest<IGetTasksResponse>(
    `${urls.tasks}?${getUserTasksQueryString({
      id,
      limit,
      offset,
      sorting,
      status,
      searchText,
      templateId,
      templateStepId,
    })}`,
    {},
    {
      timeOut: searchText ? ETimeouts.Prolonged : ETimeouts.Default,
    }
  );
}

export function getUserTasksQueryString({
  id,
  limit,
  offset,
  sorting,
  templateId,
  templateStepId,
  status,
  searchText,
}: IGetTasksConfig) {
  const IS_STATUS_COMPLETED = (status === ETaskListCompletionStatus.Completed);

  return [
    `limit=${limit}`,
    `offset=${offset}`,
    `is_completed=${IS_STATUS_COMPLETED}`,
    searchText && `search=${searchText}`,
    id && `assigned_to=${id}`,
    (IS_STATUS_COMPLETED && sorting !== ETaskListSorting.Overdue) ?
      QS_BY_SORTING_COMPLETE[sorting] :
      QS_BY_SORTING[sorting],
    templateId && `template_id=${templateId}`,
    templateStepId && `template_task_id=${templateStepId}`,
  ].filter(Boolean).join('&');
}

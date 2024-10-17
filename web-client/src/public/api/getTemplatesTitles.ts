import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { formatDateToQuery } from '../utils/dateTime';
import { ITemplateTitle } from '../types/template';
import { EWorkflowsStatus } from '../types/workflow';

export type TGetTemplatesTitlesResponse = ITemplateTitle[];

export interface IGetTemplatesTitlesRequesConfig {
  eventDateFrom?: Date;
  eventDateTo?: Date;
  fetchActive?: boolean;
  withTasksInProgress?: boolean;
  withRunningWorkflows?: boolean;
  workflowStatus?: EWorkflowsStatus;
}

export function getTemplatesTitles(config: IGetTemplatesTitlesRequesConfig = {}) {
  const { api: { urls }} = getBrowserConfigEnv();
  const baseUrl = urls.templatesTitles;
  const query = getTemplatesTitlesQueryString(config);
  const url = `${baseUrl}${query}`;

  return commonRequest<TGetTemplatesTitlesResponse>(
    url,
    {},
    { shouldThrow: true },
  );
}

export function getTemplatesTitlesQueryString({
  eventDateFrom,
  eventDateTo,
  fetchActive,
  withTasksInProgress,
  withRunningWorkflows,
  workflowStatus,
}: IGetTemplatesTitlesRequesConfig = {}) {

  const params = [
    eventDateFrom && `event_date_from=${formatDateToQuery(eventDateFrom)}`,
    eventDateTo && `event_date_to=${formatDateToQuery(eventDateTo)}`,
    fetchActive && 'is_active=true',
    typeof withTasksInProgress === 'boolean' && `with_tasks_in_progress=${withTasksInProgress}`,
    withRunningWorkflows && 'with_running_workflows=true',
    workflowStatus && workflowStatus !== EWorkflowsStatus.All && `workflows_status=${workflowStatus}`,
  ].filter(Boolean).join('&');

  return params ? `?${params}` : '';
}

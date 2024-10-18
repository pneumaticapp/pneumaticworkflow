import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { formatDateToQuery } from '../utils/dateTime';
import { ITemplateTitle } from '../types/template';
import { EWorkflowsStatus } from '../types/workflow';

export type TGetHighlightsTitlesResponse = ITemplateTitle[];

export interface IGetHighlightsTitlesRequesConfig {
  eventDateFrom?: Date;
  eventDateTo?: Date;
  fetchActive?: boolean;
  withTasksInProgress?: boolean;
  withRunningWorkflows?: boolean;
  workflowStatus?: EWorkflowsStatus;
}

export function getHighlightsTitles(config: IGetHighlightsTitlesRequesConfig = {}) {
  const { api: { urls }} = getBrowserConfigEnv();
  const baseUrl = urls.highlightsTitles;
  const query = getHighlightsTitlesQueryString(config);
  const url = `${baseUrl}${query}`;

  return commonRequest<TGetHighlightsTitlesResponse>(
    url,
    {},
    { shouldThrow: true },
  );
}

export function getHighlightsTitlesQueryString({
  eventDateFrom,
  eventDateTo,
}: IGetHighlightsTitlesRequesConfig = {}) {

  const params = [
    eventDateFrom && `event_date_from=${formatDateToQuery(eventDateFrom)}`,
    eventDateTo && `event_date_to=${formatDateToQuery(eventDateTo)}`
  ].filter(Boolean).join('&');

  return params ? `?${params}` : '';
}

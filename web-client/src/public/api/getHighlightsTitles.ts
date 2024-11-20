import { toTspDate } from '../utils/dateTime';
import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
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
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const baseUrl = urls.highlightsTitles;
  const query = getHighlightsTitlesQueryString(config);
  const url = `${baseUrl}${query}`;

  return commonRequest<TGetHighlightsTitlesResponse>(url, {}, { shouldThrow: true });
}

export function getHighlightsTitlesQueryString({ eventDateFrom, eventDateTo }: IGetHighlightsTitlesRequesConfig = {}) {
  const params = [
    eventDateFrom && `date_from_tsp=${toTspDate(eventDateFrom)}`,
    eventDateTo && `date_to_tsp=${toTspDate(eventDateTo)}`,
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

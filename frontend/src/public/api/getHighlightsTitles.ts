import { toTspDate } from '../utils/dateTime';
import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateTitleBaseWithCount } from '../types/template';

export type TGetHighlightsTitlesResponse = ITemplateTitleBaseWithCount[];

export interface IGetHighlightsTitlesRequestConfig {
  eventDateFrom?: Date;
  eventDateTo?: Date;
}

export function getHighlightsTitles(config: IGetHighlightsTitlesRequestConfig = {}) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const baseUrl = urls.highlightsTitles;
  const query = getHighlightsTitlesQueryString(config);
  const url = `${baseUrl}${query}`;

  return commonRequest<TGetHighlightsTitlesResponse>(url, {}, { shouldThrow: true });
}

export function getHighlightsTitlesQueryString({ eventDateFrom, eventDateTo }: IGetHighlightsTitlesRequestConfig = {}) {
  const params = [
    eventDateFrom && `date_from_tsp=${toTspDate(eventDateFrom)}`,
    eventDateTo && `date_to_tsp=${toTspDate(eventDateTo)}`,
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

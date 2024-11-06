import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { formatDateToQuery } from '../utils/dateTime';
import { TDashboardTimeRangeDates } from '../types/dashboard';

export interface IGetDashboardCountersResponse {
  launched: number;
  ongoing: number;
  completed: number;
  snoozed: number;
  terminated: number;
}

export function getDashboardCounters(params: TDashboardTimeRangeDates) {
  const { api: { urls } } = getBrowserConfigEnv();

  const baseUrl = urls.getDashboardCounters;
  const query = getDashboardCountersQueryString(params);
  const url = `${baseUrl}${query}`;

  return commonRequest<IGetDashboardCountersResponse>(
    url,
    {},
    {
      shouldThrow: true,
    },
  );
}

export function getDashboardCountersQueryString({ startDate, endDate }: TDashboardTimeRangeDates) {
  const params = [
    `date_from=${formatDateToQuery(startDate)}`,
    `date_to=${formatDateToQuery(endDate)}`,
  ].join('&');

  return `?${params}`;
}

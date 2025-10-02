import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { TDashboardTimeRangeDates } from '../../types/dashboard';
import { TDashboardBreakdownItemResponse } from '../../types/redux';
import { toTspDate } from '../../utils/dateTime';

export function getDashboardTasksBreakdown(params: TDashboardTimeRangeDates) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const baseUrl = urls.getDashboardTasksBreakdown;
  const query = getDashboardTasksQueryString(params);
  const url = `${baseUrl}${query}`;

  return commonRequest<TDashboardBreakdownItemResponse>(
    url,
    {},
    {
      shouldThrow: true,
    },
  );
}

export function getDashboardTasksQueryString({ startDate, endDate, now }: TDashboardTimeRangeDates) {
  const params = [
    startDate && `date_from_tsp=${toTspDate(startDate)}`,
    endDate && `date_to_tsp=${toTspDate(endDate)}`,
    now && 'now=true',
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

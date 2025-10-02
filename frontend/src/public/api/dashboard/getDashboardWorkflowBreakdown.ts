import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { TDashboardTimeRangeDates } from '../../types/dashboard';
import { TDashboardBreakdownItemResponse } from '../../types/redux';
import { toTspDate } from '../../utils/dateTime';

export function getDashboardWorkflowBreakdown(params: TDashboardTimeRangeDates) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const baseUrl = urls.getDashboardWorkflowBreakdown;
  const query = getDashboardWorkflowQueryString(params);
  const url = `${baseUrl}${query}`;

  return commonRequest<TDashboardBreakdownItemResponse>(
    url,
    {},
    {
      shouldThrow: true,
    },
  );
}

export function getDashboardWorkflowQueryString({ startDate, endDate, now }: TDashboardTimeRangeDates) {
  const params = [
    startDate && `date_from_tsp=${toTspDate(startDate)}`,
    endDate && `date_to_tsp=${toTspDate(endDate)}`,
    now && 'now=true',
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

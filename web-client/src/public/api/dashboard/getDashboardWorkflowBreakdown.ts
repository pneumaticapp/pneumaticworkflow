import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { TDashboardTimeRangeDates } from '../../types/dashboard';
import { TDashboardBreakdownItemResponse } from '../../types/redux';

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
    startDate && `date_from_tsp=${startDate.getTime() / 1000}`,
    endDate && `date_to_tsp=${endDate.getTime() / 1000}`,
    now && 'now=true',
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

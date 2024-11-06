/* eslint-disable */
/* prettier-ignore */
import {
  startOfToday,
  endOfToday,
  startOfYesterday,
  endOfYesterday,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  subWeeks,
  subMonths,
} from 'date-fns';
import { EDashboardTimeRange, TDashboardTimeRangeDates } from '../../../types/dashboard';

export const DatesMap: { [key in EDashboardTimeRange]: TDashboardTimeRangeDates } = {
  [EDashboardTimeRange.Now]: {
    now: true,
  },
  [EDashboardTimeRange.Today]: {
    startDate: startOfToday(),
    endDate: endOfToday(),
  },
  [EDashboardTimeRange.Yesterday]: {
    startDate: startOfYesterday(),
    endDate: endOfYesterday(),
  },
  [EDashboardTimeRange.ThisWeek]: {
    startDate: startOfWeek(new Date(), { weekStartsOn: 1 }),
    endDate: endOfWeek(new Date(), { weekStartsOn: 1 }),
  },
  [EDashboardTimeRange.LastWeek]: {
    startDate: startOfWeek(subWeeks(new Date(), 1), { weekStartsOn: 1 }),
    endDate: endOfWeek(new Date(subWeeks(new Date(), 1)), { weekStartsOn: 1 }),
  },
  [EDashboardTimeRange.ThisMonth]: {
    startDate: startOfMonth(new Date()),
    endDate: endOfMonth(new Date()),
  },
  [EDashboardTimeRange.LastMonth]: {
    startDate: startOfMonth(subMonths(new Date(), 1)),
    endDate: endOfMonth(new Date(subMonths(new Date(), 1))),
  },
};

export const getRangeDates = (timeRange: EDashboardTimeRange) => {
  return DatesMap[timeRange];
};

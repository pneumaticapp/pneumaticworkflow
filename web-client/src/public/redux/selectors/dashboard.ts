import { EDashboardModes, IApplicationState, IDashboardStore, TDashboardBreakdownItem } from '../../types/redux';
import { EDashboardTimeRange } from '../../types/dashboard';

export const getDashboardStore = (state: IApplicationState): IDashboardStore => state.dashboard;

export const getDashboardTimeRange = (state: IApplicationState): EDashboardTimeRange => {
  return state.dashboard.timeRange;
};

export const getDashboardBreakdownItems = (state: IApplicationState): TDashboardBreakdownItem[] =>
  state.dashboard.breakdownItems;

export const getDashboardMode = (state: IApplicationState): EDashboardModes =>
  state.dashboard.mode;

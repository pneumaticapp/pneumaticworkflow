import type { EDashboardModes, IDashboardStore } from '../dashboard/types';
import type { EDashboardTimeRange, TDashboardBreakdownItem } from '../../types/dashboard';
import type { RootState } from '../store';

export const getDashboardStore = (state: RootState): IDashboardStore => state.dashboard;

export const getDashboardTimeRange = (state: RootState): EDashboardTimeRange => {
  return state.dashboard.timeRange;
};

export const getDashboardBreakdownItems = (state: RootState): TDashboardBreakdownItem[] =>
  state.dashboard.breakdownItems;

export const getDashboardMode = (state: RootState): EDashboardModes => state.dashboard.mode;

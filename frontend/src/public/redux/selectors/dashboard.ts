import { EDashboardModes, IDashboardStore, TDashboardBreakdownItem } from '../../types/redux';
import { EDashboardTimeRange } from '../../types/dashboard';
import type { RootState } from '../store';

export const getDashboardStore = (state: RootState): IDashboardStore => state.dashboard;

export const getDashboardTimeRange = (state: RootState): EDashboardTimeRange => {
  return state.dashboard.timeRange;
};

export const getDashboardBreakdownItems = (state: RootState): TDashboardBreakdownItem[] =>
  state.dashboard.breakdownItems;

export const getDashboardMode = (state: RootState): EDashboardModes => state.dashboard.mode;

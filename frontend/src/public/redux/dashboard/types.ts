import type { EDashboardTimeRange, IGettingStartedChecklist, TDashboardBreakdownItem } from '../../types/dashboard';

export interface IDashboardCounters {
  completed: number;
  inProgress: number;
  overdue: number;
  started: number;
}

export enum EDashboardModes {
  Workflows = 'dashboard.workflows',
  Tasks = 'dashboard.tasks',
}

export interface IDashboardStore {
  counters: IDashboardCounters;
  timeRange: EDashboardTimeRange;
  breakdownItems: TDashboardBreakdownItem[];
  mode: EDashboardModes;
  isLoading: boolean;
  settingsChanged: boolean;
  checklist: {
    isLoading: boolean;
    isCompleted: boolean;
    checks: IGettingStartedChecklist;
  };
}

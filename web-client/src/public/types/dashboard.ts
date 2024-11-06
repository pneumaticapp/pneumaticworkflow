export enum EDashboardTimeRange {
  Now = 'dashboard.sorting-now',
  Today = 'dashboard.sorting-today',
  Yesterday = 'dashboard.sorting-yesterday',
  ThisWeek = 'dashboard.sorting-this-week',
  LastWeek = 'dashboard.sorting-last-week',
  ThisMonth = 'dashboard.sorting-this-month',
  LastMonth  = 'dashboard.sorting-last-month',
}

export type TDashboardTimeRangeDates = {
  startDate?: Date;
  endDate?: Date;
  now?: boolean;
};

export interface IGettingStartedChecklist {
  templateCreated: boolean;
  inviteTeam: boolean;
  workflowStarted: boolean;
  templateOwnerChanged: boolean;
  conditionCreated: boolean;
  templatePublicated: boolean;
}

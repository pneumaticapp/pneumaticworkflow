export enum EDashboardTimeRange {
  Now = 'dashboard.sorting-now',
  Today = 'dashboard.sorting-today',
  Yesterday = 'dashboard.sorting-yesterday',
  ThisWeek = 'dashboard.sorting-this-week',
  LastWeek = 'dashboard.sorting-last-week',
  ThisMonth = 'dashboard.sorting-this-month',
  LastMonth = 'dashboard.sorting-last-month',
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

export interface IDashboardTask {
  id: number;
  apiName: string;
  number: number;
  name: string;
  started: number | null;
  inProgress: number;
  overdue: number;
  completed: number | null;
}

export type TDashboardBreakdownItemResponse = {
  templateId: number;
  templateName: string;
  started: number | null;
  inProgress: number;
  overdue: number;
  isActive?: boolean;
  completed: number | null;
};

export type TDashboardBreakdownItem = TDashboardBreakdownItemResponse & {
  tasks: IDashboardTask[];
  areTasksLoading: boolean;
};

import { IntlShape } from 'react-intl';
import { EWorkflowsSorting, EWorkflowsStatus, EWorkflowsView } from '../../types/workflow';


export const WORKFLOW_VIEW_STATE_STORAGE_KEY = 'workflow_view_state';

export const getWorkflowViewStorageState = ()  => {
  return localStorage.getItem(WORKFLOW_VIEW_STATE_STORAGE_KEY) as EWorkflowsView;
};

export const setWorkflowViewStorageState = (workflowView: EWorkflowsView) => {
  localStorage.setItem(WORKFLOW_VIEW_STATE_STORAGE_KEY, workflowView);
};

export function canFilterByCurrentPerformer(status: EWorkflowsStatus) {
  return status === EWorkflowsStatus.Running || status === EWorkflowsStatus.All;
}

export function canFilterByTemplateStep(status: EWorkflowsStatus) {
  return status === EWorkflowsStatus.Running || status === EWorkflowsStatus.All;
}

export function checkSortingIsIncorrect(status: EWorkflowsStatus, sorting: EWorkflowsSorting) {
  return status === EWorkflowsStatus.Completed && sorting === EWorkflowsSorting.Urgent;
}

export function getSortingsByStatus(status: EWorkflowsStatus) {
  const statusMap = {
    [EWorkflowsStatus.All]: [
      EWorkflowsSorting.DateAsc,
      EWorkflowsSorting.DateDesc,
      EWorkflowsSorting.Overdue,
      EWorkflowsSorting.Urgent,
    ],
    [EWorkflowsStatus.Running]: [
      EWorkflowsSorting.DateAsc,
      EWorkflowsSorting.DateDesc,
      EWorkflowsSorting.Overdue,
      EWorkflowsSorting.Urgent,
    ],
    [EWorkflowsStatus.Snoozed]: [
      EWorkflowsSorting.DateAsc,
      EWorkflowsSorting.DateDesc,
      EWorkflowsSorting.Overdue,
      EWorkflowsSorting.Urgent,
    ],
    [EWorkflowsStatus.Completed]: [EWorkflowsSorting.DateAsc, EWorkflowsSorting.DateDesc, EWorkflowsSorting.Overdue],
  };

  return statusMap[status];
}

type TVerboseWorkflowSorting = {
  id: EWorkflowsSorting;
  name: string;
};

export function getVerboseSortings(
  sortings: EWorkflowsSorting[],
  formatMessage: IntlShape['formatMessage'],
): TVerboseWorkflowSorting[] {
  const objectsMap = {
    [EWorkflowsSorting.DateDesc]: { id: EWorkflowsSorting.DateDesc, name: formatMessage({ id: 'sorting.date-desc' }) },
    [EWorkflowsSorting.DateAsc]: { id: EWorkflowsSorting.DateAsc, name: formatMessage({ id: 'sorting.date-asc' }) },
    [EWorkflowsSorting.Overdue]: { id: EWorkflowsSorting.Overdue, name: formatMessage({ id: 'sorting.overdue' }) },
    [EWorkflowsSorting.Urgent]: { id: EWorkflowsSorting.Urgent, name: formatMessage({ id: 'sorting.urgent' }) },
  };

  return sortings.map((sorting) => objectsMap[sorting]);
}

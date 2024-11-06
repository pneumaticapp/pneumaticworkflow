/* eslint-disable */
/* prettier-ignore */
import { IDashboardTask, TDashboardBreakdownItem, TDashboardBreakdownItemResponse } from '../types/redux';

export function normalizeBreakdownItems(items: TDashboardBreakdownItemResponse[]): TDashboardBreakdownItem[] {
  return items
    .map(item => ({ ...item, tasks: [], areTasksLoading: false }))
    .sort((a, b) => getAciveTasksCount(a) > 0 && getAciveTasksCount(b) === 0 ? -1 : 1)
    .sort((a, b) => a.isActive && !b.isActive ? -1 : 1);
}

export function getTotalTasksCount(task: IDashboardTask | TDashboardBreakdownItem) {
  return [task.completed, task.inProgress, task.started, task.overdue]
    .map(Number)
    .reduce((acc, tasksCount) => acc + tasksCount);
}

export function getAciveTasksCount(task: TDashboardBreakdownItem) {
  return [task.inProgress, task.started]
    .map(Number)
    .reduce((acc, tasksCount) => acc + tasksCount);
}

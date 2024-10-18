import { ERoutes } from '../constants/routes';

export function getTaskDetailRoute(id: number) {
  return ERoutes.TaskDetail.replace(':id', String(id));
}

export function isTaskDetailRoute(pathname: string) {
  const taskDetailRegExp = /\/tasks\/\d+/i;

  return taskDetailRegExp.test(pathname);
}

export function getTemplateEditRoute(id: number) {
  return ERoutes.TemplatesEdit.replace(':id', String(id));
}

export function getWorkflowDetailedRoute(id: number) {
  return ERoutes.WorkflowDetail.replace(':id', String(id));
}

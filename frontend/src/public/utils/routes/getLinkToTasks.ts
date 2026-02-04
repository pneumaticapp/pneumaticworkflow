import { ERoutes } from '../../constants/routes';
import { ETaskListCompleteSorting, ETaskListCompletionStatus, ETaskListSorting } from '../../types/tasks';
import { isArrayWithItems } from '../helpers';

type TGetLinkToTasks = {
  templateId?: number;
  taskApiNAme?: string;
  status?: ETaskListCompletionStatus;
  sorting?: ETaskListSorting | ETaskListCompleteSorting;
};

export function getLinkToTasks({ templateId, status, sorting, taskApiNAme }: TGetLinkToTasks) {
  const queryParams = [
    templateId && `template=${templateId}`,
    taskApiNAme && `template-task=${taskApiNAme}`,
    status && `status=${status}`,
    sorting && `sorting=${sorting}`,
  ].filter(Boolean);
  const queryString = isArrayWithItems(queryParams) ? `?${queryParams.join('&')}` : '';

  return `${ERoutes.Tasks}${queryString}`;
}

import { ERoutes } from '../../constants/routes';
import { ETaskListCompleteSorting, ETaskListCompletionStatus, ETaskListSorting } from '../../types/tasks';
import { isArrayWithItems } from '../helpers';

type TGetLinkToTasks = {
  templateId?: number;
  stepId?: number;
  status?: ETaskListCompletionStatus;
  sorting?: ETaskListSorting | ETaskListCompleteSorting;
};

export function getLinkToTasks({ templateId, stepId, status, sorting }: TGetLinkToTasks) {
  const queryParams = [
    templateId && `template=${templateId}`,
    stepId && `template-step=${stepId}`,
    status && `status=${status}`,
    sorting && `sorting=${sorting}`,
  ].filter(Boolean);
  const queryString = isArrayWithItems(queryParams) ? `?${queryParams.join('&')}` : '';

  return `${ERoutes.Tasks}${queryString}`;
}

import { ERoutes } from '../../constants/routes';
import { EWorkflowsSorting, EWorkflowsStatus } from '../../types/workflow';
import { isArrayWithItems } from '../helpers';

type TGetLinkToWorkflows = {
  templateId?: number;
  taskApiName?: string;
  status?: EWorkflowsStatus;
  sorting?: EWorkflowsSorting;
};

export function getLinkToWorkflows({ templateId, taskApiName, status, sorting }: TGetLinkToWorkflows) {
  const queryParams = [
    templateId && `templates=${templateId}`,
    taskApiName && `tasks=${taskApiName}`,
    status && `type=${status}`,
    sorting && `sorting=${sorting}`,
  ].filter(Boolean);
  const queryString = isArrayWithItems(queryParams) ? `?${queryParams.join('&')}` : '';

  return `${ERoutes.Workflows}${queryString}`;
}

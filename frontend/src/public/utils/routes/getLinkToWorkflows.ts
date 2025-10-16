import { ERoutes } from '../../constants/routes';
import { EWorkflowsSorting, EWorkflowsStatus } from '../../types/workflow';
import { isArrayWithItems } from '../helpers';

type TGetLinkToWorkflows = {
  templateId?: number;
  stepId?: number;
  status?: EWorkflowsStatus;
  sorting?: EWorkflowsSorting;
};

export function getLinkToWorkflows({ templateId, stepId, status, sorting }: TGetLinkToWorkflows) {
  const queryParams = [
    templateId && `templates=${templateId}`,
    stepId && `steps=${stepId}`,
    status && `type=${status}`,
    sorting && `sorting=${sorting}`,
  ].filter(Boolean);
  const queryString = isArrayWithItems(queryParams) ? `?${queryParams.join('&')}` : '';

  return `${ERoutes.Workflows}${queryString}`;
}

import { ERoutes } from '../../constants/routes';
import { EWorkflowsSorting, EWorkflowsStatus } from '../../types/workflow';
import { isArrayWithItems } from '../helpers';

type TGetLinkToWorkflows = {
  templateId?: number;
  stepId?: number;
  status?: EWorkflowsStatus;
  sorting?: EWorkflowsSorting;
  fields?: string;
};

export function getLinkToWorkflows({ templateId, stepId, status, sorting, fields }: TGetLinkToWorkflows) {
  const queryParams = [
    templateId && `templates=${templateId}`,
    stepId && `steps=${stepId}`,
    status && `type=${status}`,
    sorting && `sorting=${sorting}`,
    fields && `fields=${fields}`,
  ].filter(Boolean);
  const queryString = isArrayWithItems(queryParams) ? `?${queryParams.join('&')}` : '';

  return `${ERoutes.Workflows}${queryString}`;
}

import { commonRequest } from './commonRequest';
import { ITemplateStep } from '../types/tasks';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IGetTemplateStepsRequest {
  id: number;
  withTasksInProgress?: boolean;
  isRunningWorkflows?: boolean;
  signal?: AbortSignal;
}

export function getTemplateSteps({ id, signal, ...config }: IGetTemplateStepsRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const baseUrl = urls.templateSteps.replace(':id', String(id));
  const query = getQueryString(config);
  const url = `${baseUrl}${query}`;

  return commonRequest<ITemplateStep[]>(url, { signal }, { shouldThrow: true });
}

function getQueryString({
  withTasksInProgress,
  isRunningWorkflows,
}: Pick<IGetTemplateStepsRequest, 'withTasksInProgress' | 'isRunningWorkflows'>) {
  const params = [
    typeof withTasksInProgress === 'boolean' && `with_tasks_in_progress=${withTasksInProgress}`,
    isRunningWorkflows && 'is_running_workflows=true',
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

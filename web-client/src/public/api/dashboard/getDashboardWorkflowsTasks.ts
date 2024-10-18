import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IDashboardTask } from '../../types/redux';

export type IWorkflowsByTasksRequestConfig = {
  templateId: string;
  startDate?: Date;
  endDate?: Date;
  now?: boolean;
};

export function getDashboardWorkflowsTasks(params: IWorkflowsByTasksRequestConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const baseUrl = urls.getDashboardWorkflowsTasks;
  const query = getDashboardWorkflowsTasksQueryString(params);
  const url = `${baseUrl}${query}`;

  return commonRequest<IDashboardTask[]>(
    url,
    {},
    {
      shouldThrow: true,
    },
  );
}

export function getDashboardWorkflowsTasksQueryString({
  templateId,
  startDate,
  endDate,
  now,
}: IWorkflowsByTasksRequestConfig) {
  const params = [
    `template_id=${templateId}`,
    startDate && `date_from_tsp=${startDate.getTime() / 1000}`,
    endDate && `date_to_tsp=${endDate.getTime() / 1000}`,
    now && 'now=true',
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

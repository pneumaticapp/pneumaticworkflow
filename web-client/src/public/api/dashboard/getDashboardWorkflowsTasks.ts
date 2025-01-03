import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IDashboardTask } from '../../types/redux';
import { toTspDate } from '../../utils/dateTime';

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
    startDate && `date_from_tsp=${toTspDate(startDate)}`,
    endDate && `date_to_tsp=${toTspDate(endDate)}`,
    now && 'now=true',
  ]
    .filter(Boolean)
    .join('&');

  return params ? `?${params}` : '';
}

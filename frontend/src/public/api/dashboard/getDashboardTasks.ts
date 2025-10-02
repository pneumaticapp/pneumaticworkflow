import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IDashboardTask } from '../../types/redux';
import { toTspDate } from '../../utils/dateTime';

export type TasksByStepParams = {
  templateId: string;
  startDate?: Date;
  endDate?: Date;
  now?: boolean;
};

export function getDashboardTasksBySteps(params: TasksByStepParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const baseUrl = urls.getDashboardTasksByStep;
  const query = getDashboardTasksByStepQueryString(params);
  const url = `${baseUrl}${query}`;

  return commonRequest<IDashboardTask[]>(
    url,
    {},
    {
      shouldThrow: true,
    },
  );
}

export function getDashboardTasksByStepQueryString({ templateId, startDate, endDate, now }: TasksByStepParams) {
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

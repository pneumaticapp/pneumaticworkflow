import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ETaskListCompletionStatus } from '../types/tasks';
import { ITemplateTitleBaseWithCount } from '../types/template';

export type TGetTemplatesTitlesByTasksResponse = ITemplateTitleBaseWithCount[];

export function getTemplatesTitlesByTasks(completionStatus: ETaskListCompletionStatus) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const baseUrl = urls.templatesTitlesByTasks;
  const query = getTemplatesTitlesQueryString(completionStatus);
  const url = `${baseUrl}${query}`;

  return commonRequest<TGetTemplatesTitlesByTasksResponse>(url, {}, { shouldThrow: true });
}

export function getTemplatesTitlesQueryString(completionStatus: ETaskListCompletionStatus) {
  return completionStatus === ETaskListCompletionStatus.Active ? `?status=active` : `?status=completed`;
}

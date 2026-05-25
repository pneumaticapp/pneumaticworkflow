import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateTitleBaseWithCount } from '../types/template';
import { EWorkflowsStatus } from '../types/workflow';

export type TGetTemplatesTitlesResponse = ITemplateTitleBaseWithCount[];

export function getTemplatesTitles(workflowStatus: EWorkflowsStatus) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const baseUrl = urls.templatesTitles;
  const query = getTemplatesTitlesQueryString(workflowStatus);
  const url = `${baseUrl}${query}`;

  return commonRequest<TGetTemplatesTitlesResponse>(url, {}, { shouldThrow: true });
}

export function getTemplatesTitlesQueryString(workflowStatus: EWorkflowsStatus) {
  return workflowStatus !== EWorkflowsStatus.All ? `?status=${workflowStatus}` : '';
}

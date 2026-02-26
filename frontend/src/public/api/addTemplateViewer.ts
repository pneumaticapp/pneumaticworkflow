import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateViewerResponse } from './getTemplateViewers';

export interface IAddTemplateViewerRequest {
  type: 'user' | 'group';
  user_id?: number;
  group_id?: number;
}

export function addTemplateViewer(templateId: number, data: IAddTemplateViewerRequest) {
  const { api: { urls } } = getBrowserConfigEnv();

  const url = `${urls.templates}${templateId}/add-viewer/`;

  return commonRequest<ITemplateViewerResponse>(
    url,
    {
      method: 'POST',
      data: data,
      headers: {
        'Content-Type': 'application/json',
      },
    },
    { shouldThrow: true },
  );
}
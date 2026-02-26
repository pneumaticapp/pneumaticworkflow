import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IRemoveTemplateViewerResponse {
  message: string;
}

export function removeTemplateViewer(templateId: number, viewerId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  const url = `${urls.templates}${templateId}/remove-viewer/${viewerId}/`;

  return commonRequest<IRemoveTemplateViewerResponse>(
    url,
    {
      method: 'DELETE',
    },
    { shouldThrow: true },
  );
}
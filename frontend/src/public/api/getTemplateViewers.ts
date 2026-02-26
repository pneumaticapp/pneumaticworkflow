import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface ITemplateViewerResponse {
  id: number;
  api_name: string;
  type: 'user' | 'group';
  user_details?: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  group_details?: {
    id: number;
    name: string;
  };
}

export function getTemplateViewers(templateId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  const url = `${urls.templates}${templateId}/viewers/`;

  return commonRequest<ITemplateViewerResponse[]>(
    url,
    {},
    { shouldThrow: true },
  );
}
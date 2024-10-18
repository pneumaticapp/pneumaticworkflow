import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateRequest, ITemplateResponse } from '../types/template';
import { mapRequestBody } from '../utils/mappers';

import { commonRequest } from './commonRequest';

export function createTemplate(template: ITemplateRequest) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<ITemplateResponse>(
    urls.templates,
    {
      body: mapRequestBody(template),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

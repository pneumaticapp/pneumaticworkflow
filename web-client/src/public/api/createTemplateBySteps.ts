import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateResponse, TTemplateWithTasksOnly } from '../types/template';
import { mapRequestBody } from '../utils/mappers';

import { commonRequest } from './commonRequest';

export function createTemplateBySteps(template: TTemplateWithTasksOnly) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<ITemplateResponse>(
    urls.templateBySteps,
    {
      body: mapRequestBody(template),
      method: 'POST',
    },
    { shouldThrow: true, responseType: 'empty' },
  );
}

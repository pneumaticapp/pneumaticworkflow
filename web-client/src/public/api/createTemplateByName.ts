import { ITemplate } from '../types/template';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

import { commonRequest } from './commonRequest';

export function createTemplateByName(template: TCreateTemplateByNameRequest) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.templateByName,
    {
      body: mapRequestBody(template),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}

export type TCreateTemplateByNameRequest = Pick<ITemplate, 'name'>

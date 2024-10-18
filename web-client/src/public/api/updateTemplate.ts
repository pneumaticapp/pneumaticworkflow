import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { ITemplateRequest, ITemplateResponse } from '../types/template';

export function updateTemplate(id: number, template: ITemplateRequest) {
  const { api: { urls }} = getBrowserConfigEnv();

  const url = urls.template.replace(':id', String(id));

  return commonRequest<ITemplateResponse>(
    url,
    {
      body: mapRequestBody(template),
      method: 'PUT',
    }, {
      shouldThrow: true,
    },
  );
}

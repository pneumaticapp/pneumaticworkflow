import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import type { ITemplateResponse } from '../types/template';

export function deleteTemplate(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.template.replace(':id', String(id));

  return commonRequest<ITemplateResponse>(url, { method: 'DELETE' }, { shouldThrow: true, responseType: 'empty' });
}

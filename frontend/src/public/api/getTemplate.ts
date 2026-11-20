import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import type { ITemplateResponse } from '../types/template';

export function getTemplate(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.template.replace(':id', String(id));

  return commonRequest<ITemplateResponse>(url, {}, { shouldThrow: true });
}

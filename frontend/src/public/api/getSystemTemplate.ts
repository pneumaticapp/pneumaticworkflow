import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateResponse } from '../types/template';

export function getSystemTemplate(id: string) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest<ITemplateResponse>(
    urls.systemTemplate.replace(':id', id),
    { method: 'POST' },
    { shouldThrow: true },
  );
}

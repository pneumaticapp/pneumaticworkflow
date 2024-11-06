import { commonRequest } from './commonRequest';
import { ETimeouts } from '../constants/defaultValues';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateResponse } from '../types/template';

export function copyTemplate(id: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<ITemplateResponse>(
    urls.copyTemplate.replace(':id', String(id)),
    { method: 'POST' },
    { shouldThrow: true, timeOut: ETimeouts.Short },
  );
}

import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { TTemplatePreset, TAddTemplatePreset } from '../types/template';

export function addTemplatePreset(templateId: number, newPreset: TAddTemplatePreset) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<TTemplatePreset>(
    urls.addTemplatePreset.replace(':id', String(templateId)),
    {
      method: 'POST',
      data: mapRequestBody(newPreset),
    },
    {
      shouldThrow: true,
    },
  );
}

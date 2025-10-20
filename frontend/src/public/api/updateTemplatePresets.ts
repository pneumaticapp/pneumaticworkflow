import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { TTemplatePreset } from '../types/template';

export function updateTemplatePresets(preset: TTemplatePreset) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.updateTemplatePreset.replace(':id', String(preset.id));

  return commonRequest<TTemplatePreset>(
    url,
    {
      data: mapRequestBody(preset),
      method: 'PUT',
    },
    {
      shouldThrow: true,
    },
  );
}

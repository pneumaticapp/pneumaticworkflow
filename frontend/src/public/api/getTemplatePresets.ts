import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { TTemplatePreset } from '../types/template';

export type TGetTemplatePresetsResponse = TTemplatePreset[];

export function getTemplatePresets(id: string) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.templatePresets.replace(':id', String(id));

  return commonRequest<TGetTemplatePresetsResponse>(url);
}

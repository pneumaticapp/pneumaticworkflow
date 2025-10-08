import { TGetTemplatePresetsResponse } from '../../../api/getTemplatePresets';
import { TTemplatePreset } from '../../../types/template';

export function getCorrectPresetFields(presets: TGetTemplatePresetsResponse) {
  if (presets.length === 0) {
    return undefined;
  }
  const defaultPresets: TTemplatePreset[] = presets.filter((preset) => preset.isDefault);
  let correctPreset: TTemplatePreset;
  if (defaultPresets.length > 1) {
    correctPreset = defaultPresets.find((preset) => preset.type === 'personal')!;
  } else {
    [correctPreset] = defaultPresets;
  }

  const fields = correctPreset.fields.map((field) => field.apiName);
  return fields;
}

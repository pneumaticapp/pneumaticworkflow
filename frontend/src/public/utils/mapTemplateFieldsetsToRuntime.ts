import { ITemplateResponse, IFieldsetData } from '../types/template';
import { mapFieldsetBindingsToClient } from './mapFieldsetBindingsToClient';
import { mapFieldsetBindingClientToRuntime } from './mapFieldsetBindingClientToRuntime';

export function mapTemplateFieldsetsToRuntime(template: ITemplateResponse) {
  const clientFieldsets = mapFieldsetBindingsToClient(
    template.kickoff.fieldsets || [],
  );
  const normalizedKickoff = {
    ...template.kickoff,
    fieldsets: clientFieldsets,
  };
  const normalizedTemplate = { ...template, kickoff: normalizedKickoff };
  const loadedFieldsets: IFieldsetData[] = clientFieldsets.map(
    mapFieldsetBindingClientToRuntime,
  );

  return { normalizedTemplate, loadedFieldsets };
}

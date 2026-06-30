import { ITemplateResponse } from '../types/template';
import { IFieldsetRuntime } from '../types/fieldset';
import { mapFieldsetBindingsToClient } from './mapFieldsetsAPIToClient';
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
  const loadedFieldsets: IFieldsetRuntime[] = clientFieldsets.map(
    mapFieldsetBindingClientToRuntime,
  );

  return { normalizedTemplate, loadedFieldsets };
}

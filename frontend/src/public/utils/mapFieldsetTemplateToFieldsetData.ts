/* eslint-disable */
/* prettier-ignore */
import { IFieldsetData, IExtraField } from '../types/template';

/**
 * Maps a fieldset template object (from API response, already camelCased by commonRequest)
 * into a runtime IFieldsetData used by FieldsetFieldGroup component.
 * Handles both camelCase and snake_case field names for safety.
 */
export function mapFieldsetTemplateToFieldsetData(
  fieldsetTemplate: any,
): IFieldsetData {
  const fields: IExtraField[] = (fieldsetTemplate.fields || []).map(
    (f: any, index: number) => ({
      apiName: f.apiName || f.api_name || '',
      name: f.name || '',
      description: f.description || '',
      type: f.type || 'string',
      isRequired: f.isRequired ?? f.is_required ?? false,
      isHidden: f.isHidden ?? f.is_hidden ?? false,
      order: f.order ?? index,
      value: f.default || '',
      selections: f.selections || [],
      dataset: f.dataset || null,
      userId: null,
      groupId: null,
    }),
  );

  return {
    id: fieldsetTemplate.id,
    apiName: fieldsetTemplate.apiName || fieldsetTemplate.api_name || `fieldset-${fieldsetTemplate.id}`,
    name: fieldsetTemplate.name || '',
    description: fieldsetTemplate.description || '',
    fields,
  };
}

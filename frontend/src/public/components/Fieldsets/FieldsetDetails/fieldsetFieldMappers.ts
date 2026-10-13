import { IExtraField } from '../../../types/template';

/**
 * Normalize a field object coming from the API into a proper IExtraField.
 *
 * The Axios response interceptor (commonRequest.ts) automatically converts
 * all API response keys to camelCase via `mapToCamelCase`, so by the time
 * data reaches this component the fields are ALREADY in camelCase format
 * (apiName, isRequired, isHidden, etc.) — i.e. they already match IExtraField.
 *
 * This helper just ensures default values for optional properties
 * (userId, groupId, description, etc.) so the UI components work correctly.
 */
export function normalizeFieldForUI(field: IExtraField): IExtraField {
  return {
    ...field,
    description: field.description || '',
    isRequired: field.isRequired ?? false,
    isHidden: field.isHidden ?? false,
    dataset: field.dataset ?? null,
    userId: field.userId ?? null,
    groupId: field.groupId ?? null,
  };
}

/**
 * Batch normalize: API → UI
 */
export function normalizeFieldsForUI(fields: IExtraField[]): IExtraField[] {
  return fields.map(normalizeFieldForUI);
}

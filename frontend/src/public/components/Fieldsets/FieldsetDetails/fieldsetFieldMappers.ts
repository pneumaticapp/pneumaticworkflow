import { IFieldsetField } from '../../../types/fieldset';
import { IExtraField, IExtraFieldSelection, EExtraFieldType } from '../../../types/template';
import { createFieldSelectionApiName } from '../../../utils/createId';

/**
 * Convert a single IFieldsetField (snake_case API format)
 * to IExtraField (camelCase UI format).
 */
export function mapFieldsetFieldToExtraField(field: IFieldsetField): IExtraField {
  const selections: IExtraFieldSelection[] | undefined = field.selections?.map((s) => ({
    apiName: s.api_name,
    value: s.value,
  }));

  return {
    apiName: field.api_name,
    name: field.name,
    type: field.type as EExtraFieldType,
    description: field.description || '',
    isRequired: field.is_required ?? false,
    isHidden: field.is_hidden ?? false,
    order: field.order,
    dataset: field.dataset ?? null,
    selections,
    userId: null,
    groupId: null,
  };
}

/**
 * Convert a single IExtraField (camelCase UI format)
 * to IFieldsetField (snake_case API format).
 */
export function mapExtraFieldToFieldsetField(field: IExtraField): IFieldsetField {
  const selections = field.selections
    ? (field.selections as IExtraFieldSelection[]).map((s) => ({
        api_name: s.apiName || createFieldSelectionApiName(),
        value: s.value,
      }))
    : undefined;

  return {
    api_name: field.apiName,
    name: field.name,
    type: field.type,
    description: field.description || '',
    is_required: field.isRequired ?? false,
    is_hidden: field.isHidden ?? false,
    order: field.order,
    dataset: field.dataset ?? null,
    selections,
  };
}

/**
 * Batch: API → UI
 */
export function mapFieldsetFieldsToExtraFields(fields: IFieldsetField[]): IExtraField[] {
  return fields.map(mapFieldsetFieldToExtraField);
}

/**
 * Batch: UI → API
 */
export function mapExtraFieldsToFieldsetFields(fields: IExtraField[]): IFieldsetField[] {
  return fields.map(mapExtraFieldToFieldsetField);
}

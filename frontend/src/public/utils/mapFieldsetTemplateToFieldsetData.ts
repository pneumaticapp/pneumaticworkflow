import { IFieldsetData, IExtraField, EExtraFieldType } from '../types/template';
import { EFieldLabelPosition, IFieldsetField, IFieldsetCatalogItem } from '../types/fieldset';

export function mapFieldsToExtraFields(fields: IFieldsetField[]): IExtraField[] {
  return (fields || []).map(
    (field, index) => ({
      apiName: field.apiName || '',
      name: field.name || '',
      description: field.description || '',
      type: field.type as EExtraFieldType || EExtraFieldType.String,
      isRequired: field.isRequired ?? false,
      isHidden: field.isHidden ?? false,
      order: field.order ?? index,
      value: field.default || '',
      selections: field.selections || [],
      dataset: field.dataset || null,
      userId: null,
      groupId: null,
    }),
  );
}

export function mapFieldsetTemplateToFieldsetData(
  fieldsetTemplate: IFieldsetCatalogItem,
): IFieldsetData {
  const fields = mapFieldsToExtraFields(fieldsetTemplate.fields);

  const {labelPosition} = fieldsetTemplate;
  const {rules} = fieldsetTemplate;
  const rulesCount = Array.isArray(rules) ? rules.length : 0;

  return {
    id: fieldsetTemplate.id,
    apiName: fieldsetTemplate.apiName || `fieldset-${fieldsetTemplate.id}`,
    name: fieldsetTemplate.name || '',
    description: fieldsetTemplate.description || '',
    fields,
    order: fieldsetTemplate.order ?? 0,
    labelPosition: labelPosition === EFieldLabelPosition.Left ? EFieldLabelPosition.Left : EFieldLabelPosition.Top,
    rulesCount,
  };
}

import { IFieldsetData } from '../types/template';
import { EFieldLabelPosition, IFieldsetCatalogItem } from '../types/fieldset';
import { mapFieldsToExtraFields } from './mapFieldsetBindingClientToRuntime';

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

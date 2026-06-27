import { IFieldsetBindingClient, EFieldLabelPosition } from '../types/fieldset';
import { IFieldsetData } from '../types/template';
import { mapFieldsToExtraFields } from './mapFieldsetTemplateToFieldsetData';


export function mapFieldsetBindingClientToRuntime({
  sharedFieldsetId,
  apiNameBinding,
  name,
  description,
  fields: rawFields,
  order,
  labelPosition,
  rules,
  layout,
  title,
}: IFieldsetBindingClient): IFieldsetData {
  const fields = mapFieldsToExtraFields(rawFields || []);
  const rulesCount = Array.isArray(rules) ? rules.length : 0;

  return {
    id: sharedFieldsetId,
    sharedFieldsetId,
    apiName: apiNameBinding,
    apiNameBinding,
    name: name || '',
    description: description || '',
    fields,
    order: order ?? 0,
    labelPosition: labelPosition === EFieldLabelPosition.Left
      ? EFieldLabelPosition.Left
      : EFieldLabelPosition.Top,
    rulesCount,
    layout,
    title,
    rules,
  };
}

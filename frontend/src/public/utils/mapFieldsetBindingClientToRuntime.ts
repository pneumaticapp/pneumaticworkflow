import { IFieldsetBindingClient, EFieldLabelPosition, IFieldsetField } from '../types/fieldset';
import { IFieldsetData, IExtraField, EExtraFieldType } from '../types/template';

export function mapFieldsToExtraFields(fields: IFieldsetField[]): IExtraField[] {
  return (fields || []).map(
    ({
      apiName, name, description, type, isRequired, isHidden,
      order, default: defaultValue, selections, dataset,
    }, index) => ({
      apiName: apiName || '',
      name: name || '',
      description: description || '',
      type: type as EExtraFieldType || EExtraFieldType.String,
      isRequired: isRequired ?? false,
      isHidden: isHidden ?? false,
      order: order ?? index,
      value: defaultValue || '',
      selections: selections || [],
      dataset: dataset || null,
      userId: null,
      groupId: null,
    }),
  );
}


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

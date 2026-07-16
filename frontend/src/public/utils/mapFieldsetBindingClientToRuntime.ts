import { IFieldsetBindingClient, IFieldsetRuntime, EFieldLabelPosition, IFieldsetField } from '../types/fieldset';
import { IExtraField, EExtraFieldType } from '../types/template';

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
  apiNameBinding,
  name,
  description,
  fields: rawFields,
  order,
  labelPosition,
  layout,
  title,
}: IFieldsetBindingClient): IFieldsetRuntime {
  const fields = mapFieldsToExtraFields(rawFields || []);

  return {
    apiNameBinding,
    name: name || '',
    description: description || '',
    fields,
    order: order ?? 0,
    labelPosition: labelPosition === EFieldLabelPosition.Left
      ? EFieldLabelPosition.Left
      : EFieldLabelPosition.Top,
    layout,
    title,
  };
}

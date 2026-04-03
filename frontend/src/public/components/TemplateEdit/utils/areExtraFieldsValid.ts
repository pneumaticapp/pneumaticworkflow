import { EExtraFieldType, IExtraField } from '../../../types/template';
import { validateCheckboxAndRadioField, getSelectionDuplicateError, validateKickoffFieldName } from '../../../utils/validators';

const areSelectionsValid = (field: IExtraField) => {
  if (field.dataset) return true;
  const selections = (field?.selections || []);
  const values = selections.map((selection) => selection.value);

  return selections.every((selection) => {
    if (validateCheckboxAndRadioField(selection.value)) return false;
    return !getSelectionDuplicateError(selection.value, values);
  });
};

const fieldValidateRulesMap = {
  [EExtraFieldType.Number]: () => true,
  [EExtraFieldType.Text]: () => true,
  [EExtraFieldType.String]: () => true,
  [EExtraFieldType.Url]: () => true,
  [EExtraFieldType.Date]: () => true,
  [EExtraFieldType.Checkbox]: areSelectionsValid,
  [EExtraFieldType.Creatable]: areSelectionsValid,
  [EExtraFieldType.Radio]: areSelectionsValid,
  [EExtraFieldType.File]: () => true,
  [EExtraFieldType.User]: () => true,
};

export function areExtraFieldsValid(fields: IExtraField[]) {
  return fields.every((field) => !validateKickoffFieldName(field.name) && fieldValidateRulesMap[field.type](field));
}

/* eslint-disable */
/* prettier-ignore */
import { EExtraFieldType, IExtraField } from '../../../types/template';
import { validateKickoffFieldName, validateCheckboxAndRadioField } from '../../../utils/validators';

const areSelectionsValid = (field: IExtraField) => {
  return field?.selections?.every(selection => !validateCheckboxAndRadioField(selection.value));
};

const fieldValidateRulesMap = {
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
  return fields.every(field => !validateKickoffFieldName(field.name) && fieldValidateRulesMap[field.type](field));
}

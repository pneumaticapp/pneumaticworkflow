import { EExtraFieldType, IExtraField, IExtraFieldSelection } from '../../../types/template';
import {
  validateCheckboxAndRadioField,
  getSelectionDuplicateError,
  validateKickoffFieldName,
} from '../../../utils/validators';

const FIELD_TYPES_WITH_SELECTIONS = [EExtraFieldType.Checkbox, EExtraFieldType.Creatable, EExtraFieldType.Radio];

export function getExtraFieldErrorId(field: IExtraField): string {
  const nameErrorId = validateKickoffFieldName(field.name);
  if (nameErrorId) return nameErrorId;
  if (!FIELD_TYPES_WITH_SELECTIONS.includes(field.type) || field.dataset) return '';

  const selections = (field.selections || []) as IExtraFieldSelection[];
  const values = selections.map((selection) => selection.value);

  return (
    selections
      .map(
        (selection) =>
          validateCheckboxAndRadioField(selection.value) || getSelectionDuplicateError(selection.value, values),
      )
      .find(Boolean) || ''
  );
}

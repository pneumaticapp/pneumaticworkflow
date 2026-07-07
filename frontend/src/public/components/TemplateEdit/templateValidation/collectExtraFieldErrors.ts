import { EExtraFieldType, IExtraField, IExtraFieldSelection } from '../../../types/template';
import {
  getSelectionDuplicateError,
  validateCheckboxAndRadioField,
  validateKickoffFieldName,
} from '../../../utils/validators';
import { TTemplateValidationError, TTemplateValidationScrollTarget } from './types';

const SELECTION_FIELD_TYPES = new Set([
  EExtraFieldType.Checkbox,
  EExtraFieldType.Creatable,
  EExtraFieldType.Radio,
]);

function collectSelectionErrors(
  field: IExtraField,
  pathPrefix: string,
  scrollTarget: TTemplateValidationScrollTarget,
): TTemplateValidationError[] {
  if (field.dataset || !SELECTION_FIELD_TYPES.has(field.type)) {
    return [];
  }

  const selections = (field.selections || []) as IExtraFieldSelection[];
  const values = selections.map((selection) => selection.value);
  const errors: TTemplateValidationError[] = [];

  selections.forEach((selection) => {
    const standardError = validateCheckboxAndRadioField(selection.value);
    if (standardError) {
      errors.push({
        path: `${pathPrefix}.fields.${field.apiName}.selections.${selection.apiName}`,
        messageId: standardError,
        scrollTarget,
      });
    }

    const duplicateError = getSelectionDuplicateError(selection.value, values);
    if (duplicateError) {
      errors.push({
        path: `${pathPrefix}.fields.${field.apiName}.selections.${selection.apiName}.duplicate`,
        messageId: duplicateError,
        scrollTarget,
      });
    }
  });

  return errors;
}

export function collectExtraFieldErrors(
  fields: IExtraField[],
  pathPrefix: string,
  scrollTargetForField: (fieldApiName: string) => TTemplateValidationScrollTarget,
): TTemplateValidationError[] {
  const errors: TTemplateValidationError[] = [];

  fields.forEach((field) => {
    const scrollTarget = scrollTargetForField(field.apiName);
    const nameError = validateKickoffFieldName(field.name);

    if (nameError) {
      errors.push({
        path: `${pathPrefix}.fields.${field.apiName}.name`,
        messageId: nameError,
        scrollTarget,
      });
    }

    errors.push(...collectSelectionErrors(field, pathPrefix, scrollTarget));
  });

  return errors;
}

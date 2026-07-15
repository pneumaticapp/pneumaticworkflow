import { numberRegex } from '../../constants/defaultValues';
import { IFieldsetField, IFieldsetTemplateRule } from '../../types/fieldset';
import { EExtraFieldType } from '../../types/template';
import {
  FIELDSET_RULES_MSG_FIELDS_NUMBER,
  FIELDSET_RULES_MSG_FIELDS_REQUIRED,
  FIELDSET_RULES_MSG_INCOMPLETE,
  FIELDSET_RULES_MSG_VALUE_NUMBER,
  FIELDSET_RULES_MSG_VALUE_REQUIRED,
  NUMBER_RULE_TYPES,
} from './constants';

export function validateFieldsetRules(
  fieldsetRules: IFieldsetTemplateRule[],
  availableFields: Array<Pick<IFieldsetField, 'apiName' | 'type'>> = [],
): string {
  const fieldsByApiName = new Map(availableFields.map((field) => [field.apiName, field]));

  for (let i = 0; i < fieldsetRules.length; i += 1) {
    const fieldsetRule = fieldsetRules[i];
    const value = fieldsetRule.value?.trim() ?? '';
    const hasFields = (fieldsetRule.fields?.length ?? 0) > 0;
    const hasValue = Boolean(value);

    if (!hasValue && !hasFields) {
      return FIELDSET_RULES_MSG_INCOMPLETE;
    }

    if (!hasValue) {
      return FIELDSET_RULES_MSG_VALUE_REQUIRED;
    }

    if (NUMBER_RULE_TYPES.has(fieldsetRule.type) && !numberRegex.test(value)) {
      return FIELDSET_RULES_MSG_VALUE_NUMBER;
    }

    if (!hasFields) {
      return FIELDSET_RULES_MSG_FIELDS_REQUIRED;
    }

    if (NUMBER_RULE_TYPES.has(fieldsetRule.type)) {
      const hasNonNumberField = fieldsetRule.fields.some((fieldApiName) => {
        const field = fieldsByApiName.get(fieldApiName);
        return !field || field.type !== EExtraFieldType.Number;
      });

      if (hasNonNumberField) {
        return FIELDSET_RULES_MSG_FIELDS_NUMBER;
      }
    }
  }

  return '';
}

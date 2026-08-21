import { numberRegex } from '../../constants/defaultValues';
import { IFieldsetField, IFieldsetRuleSet } from '../../types/fieldset';
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
  fieldsetRules: IFieldsetRuleSet[],
  availableFields: Array<Pick<IFieldsetField, 'apiName' | 'type'>> = [],
): string {
  const fieldsByApiName = new Map(availableFields.map((field) => [field.apiName, field]));

  for (let i = 0; i < fieldsetRules.length; i += 1) {
    const fieldsetRule = fieldsetRules[i];
    const hasFields = (fieldsetRule.fields?.length ?? 0) > 0;

    const rules = fieldsetRule.groupsOr?.flatMap((groupOr) => groupOr.groupsAnd || []) ?? [];

    if (rules.length === 0 && !hasFields) {
      return FIELDSET_RULES_MSG_INCOMPLETE;
    }

    if (rules.length === 0) {
      return FIELDSET_RULES_MSG_VALUE_REQUIRED;
    }

    if (!hasFields) {
      return FIELDSET_RULES_MSG_FIELDS_REQUIRED;
    }

    for (let j = 0; j < rules.length; j += 1) {
      const rule = rules[j];
      const value = rule.value?.trim() ?? '';
      const hasValue = Boolean(value);

      if (!hasValue) {
        return FIELDSET_RULES_MSG_VALUE_REQUIRED;
      }

      if (rule.operator && NUMBER_RULE_TYPES.has(rule.operator)) {
        if (!numberRegex.test(value)) {
          return FIELDSET_RULES_MSG_VALUE_NUMBER;
        }

        const hasNonNumberField = fieldsetRule.fields.some((fieldApiName: string) => {
          const field = fieldsByApiName.get(fieldApiName);
          return !field || field.type !== EExtraFieldType.Number;
        });

        if (hasNonNumberField) {
          return FIELDSET_RULES_MSG_FIELDS_NUMBER;
        }
      }
    }
  }

  return '';
}

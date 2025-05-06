/* eslint-disable */
/* prettier-ignore */
import { ICondition, OPERATORS_WITHOUT_VALUE, TConditionRule } from '..';
import { EExtraFieldType } from '../../../../../types/template';
import { numberRegex } from '../../../../../constants/defaultValues';

export function getFilledConditions(conditions: ICondition[]) {
  return conditions.map((condition) => ({ ...condition, rules: condition.rules.filter((rule) => rule.field) }));
}

export function areConditionsValid(conditions: ICondition[]) {
  return getFilledConditions(conditions).every((condition) => areRulesValid(condition.rules));
}

function areRulesValid(rules: TConditionRule[]) {
  return rules.every((rule) => {
    if (!rule.field || !rule.fieldType || !rule.operator) {
      return false;
    }

    const ruleMustHaveValue = !OPERATORS_WITHOUT_VALUE.includes(rule.operator);
    if (ruleMustHaveValue && !rule.value) {
      return false;
    }
    return true;
  });
}

export function isNumberConditionsValid(conditions: ICondition[]) {
  return conditions.every((condition) =>
    condition.rules.every((rule) => {
      if (rule.fieldType === EExtraFieldType.Number && rule.value && !numberRegex.test(String(rule.value))) {
        return false;
      }
      return true;
    }),
  );
}

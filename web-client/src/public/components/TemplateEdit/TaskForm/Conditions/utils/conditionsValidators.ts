/* eslint-disable */
/* prettier-ignore */
import { ICondition, OPERATORS_WITHOUT_VALUE, TConditionRule } from '..';

export function getFilledConditions(conditions: ICondition[]) {
  return conditions.map(condition => ({ ...condition, rules: condition.rules.filter(rule => rule.field) }));
}

export function areConditionsValid (conditions: ICondition[]) {
  return getFilledConditions(conditions).every(condition => areRulesValid(condition.rules));
}

function areRulesValid(rules: TConditionRule[]) {
  return rules.every(rule => {
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

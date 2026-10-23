import { ICondition, TConditionRule } from '..';
import { EExtraFieldType } from '../../../../../types/template';
import { numberRegex } from '../../../../../constants/defaultValues';
import { OPERATORS_WITHOUT_VALUE } from './shared';

export function getFilledConditions(conditions: ICondition[]) {
  return conditions.map((condition) => ({
    ...condition,
    rules: condition.rules.filter((rule) => rule.fieldType === 'kickoff' || rule.field),
  }));
}

export function getConditionRuleErrorId(rule: TConditionRule): string {
  if (!rule.field && rule.fieldType !== 'kickoff') return '';
  if (!rule.fieldType || !rule.operator) return 'validation.condition-incomplete';
  if (!OPERATORS_WITHOUT_VALUE.includes(rule.operator) && !rule.value) return 'validation.condition-incomplete';
  if (rule.fieldType === EExtraFieldType.Number && rule.value && !numberRegex.test(String(rule.value))) {
    return 'validation.number-invalid-format';
  }

  return '';
}

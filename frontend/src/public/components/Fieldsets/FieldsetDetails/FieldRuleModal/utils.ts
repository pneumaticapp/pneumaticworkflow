import {
  createFieldRuleSetApiName,
  createFieldRuleGroupOrApiName,
  createFieldRuleGroupAndApiName,
} from '../../../../utils/createId';
import {
  EFieldRuleType,
  IFieldRuleGroupAnd,
  IFieldRuleGroupOr,
  IFieldRuleSet,
} from '../../../../types/fieldset';
import { isOperatorWithoutValue } from '../RuleBase/utils';

export const createEmptyFieldRule = (): IFieldRuleGroupAnd => ({
  apiName: createFieldRuleGroupAndApiName(),
  field: null,
  operator: null,
  value: '',
});

export const createEmptyFieldRuleGroupOr = (): IFieldRuleGroupOr => ({
  apiName: createFieldRuleGroupOrApiName(),
  groupsAnd: [createEmptyFieldRule()],
});

export const createEmptyFieldRuleSet = (type: EFieldRuleType = EFieldRuleType.Validator): IFieldRuleSet => ({
  apiName: createFieldRuleSetApiName(),
  name: '',
  type,
  message: type === EFieldRuleType.Validator ? '' : null,
  order: 0,
  groupsOr: [createEmptyFieldRuleGroupOr()],
});

export const isFieldRulesetValid = (
  ruleSet: IFieldRuleSet,
): boolean => {
  if (!ruleSet.name?.trim()) {
    return false;
  }

  const rules = ruleSet.groupsOr?.flatMap((groupOr) => groupOr.groupsAnd || []) ?? [];
  if (rules.length === 0) {
    return false;
  }

  return rules.every((rule) => {
    if (ruleSet.type === EFieldRuleType.Show) {
      if (!rule.field) {
        return false;
      }
      if (!isOperatorWithoutValue(rule.operator) && !rule.value.trim()) {
        return false;
      }
      return true;
    }

    if (ruleSet.type === EFieldRuleType.Validator) {
      if (!rule.operator) {
        return false;
      }
      if (!isOperatorWithoutValue(rule.operator) && !rule.value.trim()) {
        return false;
      }
      return true;
    }

    return true;
  });
};

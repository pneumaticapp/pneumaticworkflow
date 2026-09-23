import {
  createFieldRuleSetApiName,
  createFieldRuleGroupOrApiName,
  createFieldRuleGroupAndApiName,
} from '../../../../utils/createId';
import {
  EFieldRuleType,
  IFieldRuleShowGroupAnd,
  IFieldRuleValidatorGroupAnd,
  IFieldRuleGroupOr,
  IFieldRuleSet,
} from '../../../../types/fieldset';
import { isOperatorWithoutValue } from '../RuleBase/utils';

export const createEmptyFieldRule = (): IFieldRuleValidatorGroupAnd => ({
  apiName: createFieldRuleGroupAndApiName(),
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

  if (ruleSet.type === EFieldRuleType.Show) {
    return rules.every((rule: IFieldRuleShowGroupAnd) => {
      if (!rule.field) {
        return false;
      }
      if (!isOperatorWithoutValue(rule.operator) && !rule.value.trim()) {
        return false;
      }
      return true;
    });
  }

  if (ruleSet.type === EFieldRuleType.Validator) {
    return rules.every((rule: IFieldRuleValidatorGroupAnd) => {
      if (!rule.operator) {
        return false;
      }
      if (!isOperatorWithoutValue(rule.operator) && !rule.value.trim()) {
        return false;
      }
      return true;
    });
  }

  return true;
};

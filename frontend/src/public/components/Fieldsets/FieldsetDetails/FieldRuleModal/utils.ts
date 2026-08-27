import {
  createFieldRuleSetApiName,
  createFieldRuleGroupOrApiName,
  createFieldRuleGroupAndApiName,
} from '../../../../utils/createId';
import {
  EFieldRuleValidatorOperator,
  EFieldRuleType,
  IFieldRuleGroupAnd,
  IFieldRuleGroupOr,
  IFieldRuleSet,
} from '../../../../types/fieldset';
import { EExtraFieldType } from '../../../../types/template';
import { TRuleFieldOption } from '../RuleBase/types';

export const createEmptyFieldRule = (
  type: EFieldRuleType = EFieldRuleType.Validator,
): IFieldRuleGroupAnd => ({
  apiName: createFieldRuleGroupAndApiName(),
  field: null,
  operator: type === EFieldRuleType.Validator ? EFieldRuleValidatorOperator.Equal : null,
  value: '',
});

export const createEmptyFieldRuleGroupOr = (
  type: EFieldRuleType = EFieldRuleType.Validator,
): IFieldRuleGroupOr => ({
  apiName: createFieldRuleGroupOrApiName(),
  groupsAnd: [createEmptyFieldRule(type)],
});

export const createEmptyFieldRuleSet = (type: EFieldRuleType = EFieldRuleType.Validator): IFieldRuleSet => ({
  apiName: createFieldRuleSetApiName(),
  name: '',
  type,
  message: type === EFieldRuleType.Validator ? '' : null,
  order: 0,
  groupsOr: [createEmptyFieldRuleGroupOr(type)],
});

export const traverseFieldRuleSetGroupsAnd = (
  ruleSet: IFieldRuleSet,
  changeRules: (groupsAnd: IFieldRuleGroupAnd[]) => IFieldRuleGroupAnd[],
  targetGroupOrApiName?: string,
): IFieldRuleSet => {
  const targetGroupOr = targetGroupOrApiName || ruleSet.groupsOr[0]?.apiName;
  if (!targetGroupOr) return ruleSet;

  return {
    ...ruleSet,
    groupsOr: ruleSet.groupsOr.map((groupOr) => {
      if (groupOr.apiName !== targetGroupOr) return groupOr;
      return {
        ...groupOr,
        groupsAnd: changeRules(groupOr.groupsAnd || []),
      };
    }),
  };
};

export const addFieldRule = (
  ruleSet: IFieldRuleSet,
  targetGroupOrApiName?: string,
): IFieldRuleSet =>
  traverseFieldRuleSetGroupsAnd(
    ruleSet,
    (groupsAnd) => [...groupsAnd, createEmptyFieldRule()],
    targetGroupOrApiName,
  );

export const deleteFieldRule = (
  ruleSet: IFieldRuleSet,
  ruleApiName: string,
  targetGroupOrApiName?: string,
): IFieldRuleSet =>
  traverseFieldRuleSetGroupsAnd(
    ruleSet,
    (groupsAnd) => groupsAnd.filter((rule) => rule.apiName !== ruleApiName),
    targetGroupOrApiName,
  );

export const updateFieldRule = (
  ruleSet: IFieldRuleSet,
  ruleApiName: string,
  changes: Partial<IFieldRuleGroupAnd>,
  targetGroupOrApiName?: string,
): IFieldRuleSet =>
  traverseFieldRuleSetGroupsAnd(
    ruleSet,
    (groupsAnd) =>
      groupsAnd.map((rule) =>
        rule.apiName === ruleApiName ? { ...rule, ...changes } : rule,
      ),
    targetGroupOrApiName,
  );

export const isFieldRulesetValid = (
  ruleSet: IFieldRuleSet,
  rulesFieldOptions: TRuleFieldOption[] = [],
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
      const selectedField = rulesFieldOptions.find((fieldOption) => fieldOption.apiName === rule.field);
      const isFileField = selectedField?.type === EExtraFieldType.File;
      if (!isFileField) {
        const valStr = rule.value != null ? String(rule.value).trim() : '';
        if (!valStr) {
          return false;
        }
      }
      return true;
    }

    if (ruleSet.type === EFieldRuleType.Validator) {
      const valStr = rule.value != null ? String(rule.value).trim() : '';
      if (!valStr) {
        return false;
      }
      return true;
    }

    return true;
  });
};

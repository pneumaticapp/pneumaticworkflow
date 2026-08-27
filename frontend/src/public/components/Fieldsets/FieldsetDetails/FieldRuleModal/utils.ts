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

export const createEmptyFieldRule = (
  type: EFieldRuleType = EFieldRuleType.Show,
): IFieldRuleGroupAnd => ({
  apiName: createFieldRuleGroupAndApiName(),
  field: null,
  operator: type === EFieldRuleType.Validator ? EFieldRuleValidatorOperator.Equal : null,
  value: '',
});

export const createEmptyFieldRuleGroupOr = (
  type: EFieldRuleType = EFieldRuleType.Show,
): IFieldRuleGroupOr => ({
  apiName: createFieldRuleGroupOrApiName(),
  groupsAnd: [createEmptyFieldRule(type)],
});

export const createEmptyFieldRuleSet = (type: EFieldRuleType = EFieldRuleType.Show): IFieldRuleSet => ({
  apiName: createFieldRuleSetApiName(),
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

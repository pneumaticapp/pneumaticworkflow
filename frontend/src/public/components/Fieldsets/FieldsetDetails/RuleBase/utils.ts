import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  ERuleCombinator,
} from '../../../../types/fieldset';
import { createRulesetGroupOrApiName } from '../../../../utils/createId';
import { getDropdownOperators } from '../../../TemplateEdit/TaskForm/Conditions/utils/getDropdownOperators';
import { EConditionOperators } from '../../../TemplateEdit/TaskForm/Conditions/types';
import { EExtraFieldType } from '../../../../types/template';
import { IFieldRulesetBaseOperatorOption } from './types';

const EXCLUDED_FIELDSET_OPERATORS = [
  EConditionOperators.Exist,
  EConditionOperators.NotExist,
];

export const getFieldsetRuleShowOperators = (
  fieldType: EExtraFieldType,
  messages: Record<string, string>,
): IFieldRulesetBaseOperatorOption[] => {
  const operators = getDropdownOperators(fieldType, messages);
  return operators
    .filter((item) => !EXCLUDED_FIELDSET_OPERATORS.includes(item.operator))
    .map((item) => ({
      apiName: item.operator,
      name: item.label,
    }));
};

export const traverseGroupsAnd = <T extends IBaseRuleSet>(
  ruleSet: T,
  groupOrApiName: string,
  changeRules: (groupsAnd: IBaseRuleGroupAnd[]) => IBaseRuleGroupAnd[],
): T => ({
    ...ruleSet,
    groupsOr: ruleSet.groupsOr
      .map((groupOr) => {
        if (groupOr.apiName !== groupOrApiName) return groupOr;

        return { ...groupOr, groupsAnd: changeRules(groupOr.groupsAnd || []) };
      })
      .filter((groupOr) => groupOr.groupsAnd.length > 0),
  });

export const updateRule = <T extends IBaseRuleSet>(
  ruleSet: T,
  groupOrApiName: string,
  ruleApiName: string,
  changes: Partial<IBaseRuleGroupAnd>,
): T =>
    traverseGroupsAnd(
      ruleSet,
      groupOrApiName,
      (groupsAnd) =>
        groupsAnd.map((rule) =>
          rule.apiName === ruleApiName ? { ...rule, ...changes } : rule,
        ),
    );

export const deleteRule = <T extends IBaseRuleSet>(
  ruleSet: T,
  groupOrApiName: string,
  ruleApiName: string,
): T =>
    traverseGroupsAnd(
      ruleSet,
      groupOrApiName,
      (groupsAnd) => groupsAnd.filter((rule) => rule.apiName !== ruleApiName),
    );

export const addRule = <T extends IBaseRuleSet>(
  ruleSet: T,
  createEmptyItem: () => IBaseRuleGroupAnd,
  groupOrApiName?: string,
): T => {
  const lastGroupOr = ruleSet.groupsOr[ruleSet.groupsOr.length - 1];
  const targetGroupOr = groupOrApiName || lastGroupOr?.apiName;

  if (targetGroupOr) {
    return traverseGroupsAnd(
      ruleSet,
      targetGroupOr,
      (groupsAnd) => [...groupsAnd, createEmptyItem()],
    );
  }

  return {
    ...ruleSet,
    groupsOr: [
      ...ruleSet.groupsOr,
      { apiName: createRulesetGroupOrApiName(), groupsAnd: [createEmptyItem()] },
    ],
  };
};

export const regroupRules = <T extends IBaseRuleSet>(
  ruleSet: T,
  groupOrApiName: string,
  groupAndApiName: string,
  ruleCombinator: ERuleCombinator,
): T => {
  const { groupsOr = [] } = ruleSet;

  if (ruleCombinator === ERuleCombinator.Or) {
    const newGroupsOr = groupsOr.flatMap((groupOr) => {
      if (groupOr.apiName !== groupOrApiName) return [groupOr];

      const splitIndex = groupOr.groupsAnd.findIndex(
        (groupAnd) => groupAnd.apiName === groupAndApiName,
      );
      if (splitIndex <= 0) return [groupOr];

      const before = groupOr.groupsAnd.slice(0, splitIndex);
      const after = groupOr.groupsAnd.slice(splitIndex);

      return [
        { ...groupOr, groupsAnd: before },
        { apiName: createRulesetGroupOrApiName(), groupsAnd: after },
      ];
    });

    return { ...ruleSet, groupsOr: newGroupsOr };
  }

  const groupOrIndex = groupsOr.findIndex((group) => group.apiName === groupOrApiName);
  if (groupOrIndex <= 0) return ruleSet;

  const prevGroupOr = groupsOr[groupOrIndex - 1];
  const currentGroupOr = groupsOr[groupOrIndex];
  const merged = {
    ...prevGroupOr,
    groupsAnd: [...prevGroupOr.groupsAnd, ...currentGroupOr.groupsAnd],
  };

  const newGroupsOr = [
    ...groupsOr.slice(0, groupOrIndex - 1),
    merged,
    ...groupsOr.slice(groupOrIndex + 1),
  ];

  return { ...ruleSet, groupsOr: newGroupsOr };
};

export const getRuleCombinator = (groupAndIndex: number): ERuleCombinator =>
  groupAndIndex > 0 ? ERuleCombinator.And : ERuleCombinator.Or;

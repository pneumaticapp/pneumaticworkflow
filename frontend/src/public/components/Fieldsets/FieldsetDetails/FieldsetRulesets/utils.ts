import {
  IFieldsetRuleSet,
  IFieldsetRuleGroupAnd,
  EFieldsetNumberRulesetOperator,
} from '../../../../types/fieldset';
import {
  createRulesetApiName,
  createRulesetGroupOrApiName,
  createRulesetGroupAndApiName,
} from '../../../../utils/createId';
import { TRulePath } from './types';

export const createEmptyGroupAnd = (): IFieldsetRuleGroupAnd => ({
  apiName: createRulesetGroupAndApiName(),
  operator: EFieldsetNumberRulesetOperator.SumEqual,
  value: '',
});

export const addGroupAnd = (
  rulesets: IFieldsetRuleSet[],
  rulesetApiName: string,
  ruleGroupOrApiName: string,
): IFieldsetRuleSet[] => {
  return rulesets.map((ruleset) => {
    if (ruleset.apiName !== rulesetApiName) return ruleset;

    const { groupsOr = [] } = ruleset;
    const updatedGroupsOr = groupsOr.map((groupOr) => {
      if (groupOr.apiName !== ruleGroupOrApiName) return groupOr;

      const newGroupAnd = createEmptyGroupAnd();
      return {
        ...groupOr,
        groupsAnd: [...(groupOr.groupsAnd || []), newGroupAnd],
      };
    });

    return { ...ruleset, groupsOr: updatedGroupsOr };
  });
};

export const createEmptyRuleset = (): IFieldsetRuleSet => ({
  apiName: createRulesetApiName(),
  order: 0,
  fields: [],
  groupsOr: [
    {
      apiName: createRulesetGroupOrApiName(),
      groupsAnd: [createEmptyGroupAnd()],
    },
  ],
});

export const updateRulesetFields = (
  rulesets: IFieldsetRuleSet[],
  rulesetApiName: string,
  fieldApiNames: (string | number | null)[],
): IFieldsetRuleSet[] => {
  const stringFieldApiNames = fieldApiNames.filter(
    (name): name is string => typeof name === 'string',
  );

  return rulesets.map((ruleSet) =>
    ruleSet.apiName === rulesetApiName
      ? { ...ruleSet, fields: stringFieldApiNames }
      : ruleSet,
  );
};

export const updateRuleset = (
  rulesets: IFieldsetRuleSet[],
  { rulesetApiName, ruleGroupOrApiName, ruleGroupAndApiName }: TRulePath,
  ruleChanges: Partial<IFieldsetRuleGroupAnd>,
): IFieldsetRuleSet[] => {
  return rulesets.map((ruleset) => {
    if (ruleset.apiName !== rulesetApiName) return ruleset;

    const { groupsOr = [] } = ruleset;
    const updatedGroupsOr = groupsOr.map((groupOr) => {
      if (groupOr.apiName !== ruleGroupOrApiName) return groupOr;

      const { groupsAnd = [] } = groupOr;
      const updatedGroupsAnd = groupsAnd.map((ruleGroupAnd) => {
        if (ruleGroupAnd.apiName !== ruleGroupAndApiName) return ruleGroupAnd;

        return { ...ruleGroupAnd, ...ruleChanges };
      });

      return { ...groupOr, groupsAnd: updatedGroupsAnd };
    });

    return { ...ruleset, groupsOr: updatedGroupsOr };
  });
};

export const getNormalizedRulesetOrders = (rulesets: IFieldsetRuleSet[]): IFieldsetRuleSet[] => {
  return rulesets.map((ruleSet, index) => ({
    ...ruleSet,
    order: index,
  }));
};

export const deleteGroupAnd = (
  rulesets: IFieldsetRuleSet[],
  { rulesetApiName, ruleGroupOrApiName, ruleGroupAndApiName }: TRulePath,
): IFieldsetRuleSet[] => {
  return rulesets.map((ruleset) => {
    if (ruleset.apiName !== rulesetApiName) return ruleset;

    const { groupsOr = [] } = ruleset;
    const updatedGroupsOr = groupsOr
      .map((groupOr) => {
        if (groupOr.apiName !== ruleGroupOrApiName) return groupOr;

        const { groupsAnd = [] } = groupOr;
        const updatedGroupsAnd = groupsAnd.filter(
          (ruleGroupAnd) => ruleGroupAnd.apiName !== ruleGroupAndApiName,
        );

        return { ...groupOr, groupsAnd: updatedGroupsAnd };
      })
      .filter((groupOr) => groupOr.groupsAnd.length > 0);

    return { ...ruleset, groupsOr: updatedGroupsOr };
  });
};

export const deleteRuleset = (
  rulesets: IFieldsetRuleSet[],
  rulesetApiName: string,
): IFieldsetRuleSet[] => {
  const filtered = rulesets.filter((ruleSet) => ruleSet.apiName !== rulesetApiName);
  return getNormalizedRulesetOrders(filtered);
};



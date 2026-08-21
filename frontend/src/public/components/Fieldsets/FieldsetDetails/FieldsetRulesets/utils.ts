import {
  IFieldsetRuleSet,
  IFieldsetRuleGroupAnd,
  EFieldsetNumberRulesetOperator,
  ERuleCombinator,
} from '../../../../types/fieldset';
import {
  createRulesetApiName,
  createRulesetGroupOrApiName,
  createRulesetGroupAndApiName,
} from '../../../../utils/createId';
import { TRulePath, TRulesetsParams, TRulesetParams } from './types';

const createEmptyRuleset = (): IFieldsetRuleSet => ({
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

const createEmptyGroupAnd = (): IFieldsetRuleGroupAnd => ({
  apiName: createRulesetGroupAndApiName(),
  operator: EFieldsetNumberRulesetOperator.SumEqual,
  value: '',
});

export const addRuleset = ({ rulesets, onRulesetsChange }: TRulesetsParams) => {
  onRulesetsChange(getNormalizedRulesetOrders([...rulesets, createEmptyRuleset()]));
};

export const addGroupAnd = ({
  rulesets,
  rulesetApiName,
  onRulesetsChange,
}: TRulesetParams) => {
  const ruleSet = rulesets.find((ruleset) => ruleset.apiName === rulesetApiName);
  if (!ruleSet) return;

  const lastGroupOr = ruleSet.groupsOr[ruleSet.groupsOr.length - 1];
  const newGroupAnd = createEmptyGroupAnd();

  const updatedRulesets = rulesets.map((ruleset) => {
    if (ruleset.apiName !== rulesetApiName) return ruleset;

    if (lastGroupOr) {
      const updatedGroupsOr = (ruleset.groupsOr || []).map((groupOr) => {
        if (groupOr.apiName !== lastGroupOr.apiName) return groupOr;
        return {
          ...groupOr,
          groupsAnd: [...(groupOr.groupsAnd || []), newGroupAnd],
        };
      });
      return { ...ruleset, groupsOr: updatedGroupsOr };
    }

    const newGroupOr = {
      apiName: createRulesetGroupOrApiName(),
      groupsAnd: [newGroupAnd],
    };
    return { ...ruleset, groupsOr: [...(ruleset.groupsOr || []), newGroupOr] };
  });

  onRulesetsChange(updatedRulesets);
};

export const getNormalizedRulesetOrders = (rulesets: IFieldsetRuleSet[]): IFieldsetRuleSet[] => {
  return rulesets.map((ruleSet, index) => ({
    ...ruleSet,
    order: index,
  }));
};

const traverseGroupsAnd = (
  rulesets: IFieldsetRuleSet[],
  { rulesetApiName, ruleGroupOrApiName }: Omit<TRulePath, 'ruleGroupAndApiName'>,
  changeRules: (groupsAnd: IFieldsetRuleGroupAnd[]) => IFieldsetRuleGroupAnd[],
): IFieldsetRuleSet[] => {
  return rulesets.map((ruleset) => {
    if (ruleset.apiName !== rulesetApiName) return ruleset;

    const { groupsOr = [] } = ruleset;
    const updatedGroupsOr = groupsOr
      .map((groupOr) => {
        if (groupOr.apiName !== ruleGroupOrApiName) return groupOr;

        return { ...groupOr, groupsAnd: changeRules(groupOr.groupsAnd || []) };
      })
      .filter((groupOr) => groupOr.groupsAnd.length > 0);

    return { ...ruleset, groupsOr: updatedGroupsOr };
  });
};

export const updateRuleset = ({
  rulesets,
  rulePath: { rulesetApiName, ruleGroupOrApiName, ruleGroupAndApiName },
  ruleChanges,
  onRulesetsChange,
}: TRulesetsParams & {
  rulePath: TRulePath;
  ruleChanges: Partial<IFieldsetRuleGroupAnd>;
}) => {
  const updatedRulesets = traverseGroupsAnd(
    rulesets,
    { rulesetApiName, ruleGroupOrApiName },
    (groupsAnd) => groupsAnd.map((ruleGroupAnd) =>
      ruleGroupAnd.apiName === ruleGroupAndApiName
        ? { ...ruleGroupAnd, ...ruleChanges }
        : ruleGroupAnd,
    ),
  );

  onRulesetsChange(updatedRulesets);
};

export const updateRulesetMessage = ({
  rulesets,
  rulesetApiName,
  message,
  onRulesetsChange,
}: TRulesetParams & { message: string }) => {
  const updatedRulesets = rulesets.map((ruleSet) =>
    ruleSet.apiName === rulesetApiName ? { ...ruleSet, message } : ruleSet,
  );
  onRulesetsChange(updatedRulesets);
};

export const updateRulesetFields = ({
  rulesets,
  rulesetApiName,
  fieldApiNames,
  onRulesetsChange,
}: TRulesetParams & { fieldApiNames: (string | number | null)[] }) => {
  const stringFieldApiNames = fieldApiNames.filter(
    (name): name is string => typeof name === 'string',
  );

  const updatedRulesets = rulesets.map((ruleSet) =>
    ruleSet.apiName === rulesetApiName
      ? { ...ruleSet, fields: stringFieldApiNames }
      : ruleSet,
  );
  onRulesetsChange(updatedRulesets);
};

export const deleteRuleset = ({
  rulesets,
  rulesetApiName,
  onRulesetsChange,
}: TRulesetParams) => {
  const filtered = rulesets.filter((ruleSet) => ruleSet.apiName !== rulesetApiName);
  onRulesetsChange(getNormalizedRulesetOrders(filtered));
};

export const deleteRule = ({
  rulesets,
  rulePath: { rulesetApiName, ruleGroupOrApiName, ruleGroupAndApiName },
  onRulesetsChange,
}: TRulesetsParams & { rulePath: TRulePath }) => {
  const updatedRulesets = traverseGroupsAnd(
    rulesets,
    { rulesetApiName, ruleGroupOrApiName },
    (groupsAnd) => groupsAnd.filter(
      (ruleGroupAnd) => ruleGroupAnd.apiName !== ruleGroupAndApiName,
    ),
  );

  onRulesetsChange(updatedRulesets);
};

export const removeFieldFromRuleset = ({
  rulesets,
  rulesetApiName,
  fieldApiName,
  onRulesetsChange,
}: TRulesetParams & { fieldApiName: string }) => {
  const updatedRulesets = rulesets.map((ruleSet) => {
    if (ruleSet.apiName !== rulesetApiName) return ruleSet;
    const updatedFields = (ruleSet.fields || []).filter((apiName) => apiName !== fieldApiName);
    return { ...ruleSet, fields: updatedFields };
  });

  onRulesetsChange(updatedRulesets);
};

export const regroupRules = ({
  rulesets,
  rulesetApiName,
  groupOrApiName,
  groupAndApiName,
  ruleCombinator,
  onRulesetsChange,
}: TRulesetParams & {
  groupOrApiName: string;
  groupAndApiName: string;
  ruleCombinator: ERuleCombinator;
}) => {
  const updatedRulesets = rulesets.map((ruleset) => {
    if (ruleset.apiName !== rulesetApiName) return ruleset;

    const { groupsOr = [] } = ruleset;

    if (ruleCombinator === ERuleCombinator.Or) {
      const newGroupsOr = groupsOr.flatMap((groupOr) => {
        if (groupOr.apiName !== groupOrApiName) return [groupOr];

        const splitIndex = groupOr.groupsAnd.findIndex((groupAnd) => groupAnd.apiName === groupAndApiName);
        if (splitIndex <= 0) return [groupOr];

        const before = groupOr.groupsAnd.slice(0, splitIndex);
        const after = groupOr.groupsAnd.slice(splitIndex);

        return [
          { ...groupOr, groupsAnd: before },
          { apiName: createRulesetGroupOrApiName(), groupsAnd: after },
        ];
      });

      return { ...ruleset, groupsOr: newGroupsOr };
    }

    const groupOrIndex = groupsOr.findIndex((group) => group.apiName === groupOrApiName);
    if (groupOrIndex <= 0) return ruleset;

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

    return { ...ruleset, groupsOr: newGroupsOr };
  });

  onRulesetsChange(updatedRulesets);
};

export const getRuleCombinator = (groupAndIndex: number): ERuleCombinator =>
  groupAndIndex > 0 ? ERuleCombinator.And : ERuleCombinator.Or;

export const getFieldsTooltipText = (
  hasFields: boolean,
  hasNumericFields: boolean,
  formatMessage: (descriptor: { id: string }) => string,
): string => {
  if (!hasFields) {
    return formatMessage({ id: 'fieldsets.rule-fields-disabled-tooltip' });
  }
  if (!hasNumericFields) {
    return formatMessage({ id: 'fieldsets.rule-fields-no-number-fields-tooltip' });
  }
  return '';
};

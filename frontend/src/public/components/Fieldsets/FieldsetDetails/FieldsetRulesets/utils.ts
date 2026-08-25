import {
  IBaseRuleGroupAnd,
  IFieldsetRuleGroupAnd,
  EFieldsetNumberRulesetOperator,
  ERuleCombinator,
  IFieldsetRuleSet,
} from '../../../../types/fieldset';
import {
  createRulesetApiName,
  createRulesetGroupOrApiName,
  createRulesetGroupAndApiName,
} from '../../../../utils/createId';
import { TRulesetsParams, TRulesetParams } from './types';
import {
  updateRule,
  deleteRule,
  addRule,
  regroupRules,
} from '../RuleBase/utils';

export { getRuleCombinator } from '../RuleBase/utils';

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

export const addGroupAndToRulesets = ({
  rulesets,
  rulesetApiName,
  onRulesetsChange,
}: TRulesetParams) => {
  const ruleSet = rulesets.find((ruleset) => ruleset.apiName === rulesetApiName);
  if (!ruleSet) return;

  const updatedRulesets = rulesets.map((ruleset) =>
    ruleset.apiName === rulesetApiName
      ? addRule(ruleset, createEmptyGroupAnd)
      : ruleset,
  );
  onRulesetsChange(updatedRulesets);
};

export const getNormalizedRulesetOrders = (rulesets: IFieldsetRuleSet[]): IFieldsetRuleSet[] => {
  return rulesets.map((ruleSet, index) => ({
    ...ruleSet,
    order: index,
  }));
};

export const updateRuleInRulesets = ({
  rulesets,
  rulesetApiName,
  ruleGroupOrApiName,
  ruleGroupAndApiName,
  ruleChanges,
  onRulesetsChange,
}: TRulesetsParams & {
  rulesetApiName: string;
  ruleGroupOrApiName: string;
  ruleGroupAndApiName: string;
  ruleChanges: Partial<IBaseRuleGroupAnd>;
}) => {
  const updatedRulesets = rulesets.map((ruleset) =>
    ruleset.apiName === rulesetApiName
      ? updateRule(ruleset, ruleGroupOrApiName, ruleGroupAndApiName, ruleChanges)
      : ruleset,
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

export const deleteRuleFromRulesets = ({
  rulesets,
  rulesetApiName,
  ruleGroupOrApiName,
  ruleGroupAndApiName,
  onRulesetsChange,
}: TRulesetsParams & {
  rulesetApiName: string;
  ruleGroupOrApiName: string;
  ruleGroupAndApiName: string;
}) => {
  const updatedRulesets = rulesets.map((ruleset) =>
    ruleset.apiName === rulesetApiName
      ? deleteRule(ruleset, ruleGroupOrApiName, ruleGroupAndApiName)
      : ruleset,
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

export const regroupRulesInRulesets = ({
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
  const updatedRulesets = rulesets.map((ruleset) =>
    ruleset.apiName === rulesetApiName
      ? regroupRules(ruleset, groupOrApiName, groupAndApiName, ruleCombinator)
      : ruleset,
  );
  onRulesetsChange(updatedRulesets);
};

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

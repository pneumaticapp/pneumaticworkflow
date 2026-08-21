import {
  addRuleset,
  addGroupAnd,
  getNormalizedRulesetOrders,
  updateRuleset,
  updateRulesetMessage,
  updateRulesetFields,
  deleteRuleset,
  deleteRule,
  removeFieldFromRuleset,
  regroupRules,
  getRuleCombinator,
  getFieldsTooltipText,
} from '../utils';
import { ERuleCombinator, EFieldsetNumberRulesetOperator, IFieldsetRuleSet } from '../../../../../types/fieldset';
import {
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
} from '../../../../../__stubs__/fieldsets.factory';

describe('FieldsetRulesets utils', () => {
  let onRulesetsChangeMock: jest.Mock;

  beforeEach(() => {
    onRulesetsChangeMock = jest.fn();
  });

  describe('getNormalizedRulesetOrders', () => {
    it('should assign sequential order indices to the rulesets array', () => {
      const rulesets: IFieldsetRuleSet[] = [
        makeFieldsetRuleset({ apiName: 'r1', order: 10 }),
        makeFieldsetRuleset({ apiName: 'r2', order: 25 }),
      ];

      const result = getNormalizedRulesetOrders(rulesets);

      expect(result[0].order).toBe(0);
      expect(result[1].order).toBe(1);
    });
  });

  describe('addRuleset', () => {
    it('should append a default ruleset and invoke callback with normalized orders', () => {
      const existingRuleset = makeFieldsetRuleset({ apiName: 'r1', order: 0 });

      addRuleset({
        rulesets: [existingRuleset],
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);

      const resultRulesets: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(resultRulesets).toHaveLength(2);
      expect(resultRulesets[0].apiName).toBe('r1');
      expect(resultRulesets[1].order).toBe(1);
      expect(resultRulesets[1].groupsOr).toHaveLength(1);
      expect(resultRulesets[1].groupsOr[0].groupsAnd).toHaveLength(1);
    });
  });

  describe('addGroupAnd', () => {
    it('should add a new AND rule to the last OR group of the targeted ruleset', () => {
      const groupOr = makeFieldsetRuleGroupOr({
        apiName: 'g-or-1',
        groupsAnd: [makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' })],
      });
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      addGroupAnd({
        rulesets: [ruleset],
        rulesetApiName: 'r1',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].groupsOr[0].groupsAnd).toHaveLength(2);
    });

    it('should do nothing when ruleset is not found by apiName', () => {
      const ruleset = makeFieldsetRuleset({ apiName: 'r1' });

      addGroupAnd({
        rulesets: [ruleset],
        rulesetApiName: 'non-existent',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).not.toHaveBeenCalled();
    });
  });

  describe('updateRuleset', () => {
    it('should modify target AND rule properties (operator, value)', () => {
      const groupAnd = makeFieldsetRuleGroupAnd({
        apiName: 'g-and-1',
        operator: EFieldsetNumberRulesetOperator.SumEqual,
        value: '10',
      });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd] });
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      updateRuleset({
        rulesets: [ruleset],
        rulePath: {
          rulesetApiName: 'r1',
          ruleGroupOrApiName: 'g-or-1',
          ruleGroupAndApiName: 'g-and-1',
        },
        ruleChanges: {
          operator: EFieldsetNumberRulesetOperator.SumGreaterThan,
          value: '50',
        },
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      const targetRule = updated[0].groupsOr[0].groupsAnd[0];

      expect(targetRule.operator).toBe(EFieldsetNumberRulesetOperator.SumGreaterThan);
      expect(targetRule.value).toBe('50');
    });
  });

  describe('updateRulesetMessage', () => {
    it('should update custom error message for targeted ruleset', () => {
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', message: 'Old' });

      updateRulesetMessage({
        rulesets: [ruleset],
        rulesetApiName: 'r1',
        message: 'New message',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated[0].message).toBe('New message');
    });
  });

  describe('updateRulesetFields', () => {
    it('should filter non-string values and keep valid field apiNames', () => {
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', fields: [] });

      updateRulesetFields({
        rulesets: [ruleset],
        rulesetApiName: 'r1',
        fieldApiNames: ['field-1', null, 123, 'field-2'],
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated[0].fields).toEqual(['field-1', 'field-2']);
    });
  });

  describe('deleteRuleset & deleteRule', () => {
    it('should remove entire ruleset and normalize order of remaining rulesets', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', order: 0 });
      const r2 = makeFieldsetRuleset({ apiName: 'r2', order: 1 });

      deleteRuleset({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated).toHaveLength(1);
      expect(updated[0].apiName).toBe('r2');
      expect(updated[0].order).toBe(0);
    });

    it('should delete AND rule and remove empty OR group', () => {
      const groupAnd = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd] });
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      deleteRule({
        rulesets: [ruleset],
        rulePath: {
          rulesetApiName: 'r1',
          ruleGroupOrApiName: 'g-or-1',
          ruleGroupAndApiName: 'g-and-1',
        },
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated[0].groupsOr).toHaveLength(0);
    });

    it('should remove targeted field from fields array', () => {
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', fields: ['f1', 'f2'] });

      removeFieldFromRuleset({
        rulesets: [ruleset],
        rulesetApiName: 'r1',
        fieldApiName: 'f1',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated[0].fields).toEqual(['f2']);
    });
  });

  describe('regroupRules', () => {
    it('should split rules into a new OR group when using ERuleCombinator.Or', () => {
      const gAnd1 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const gAnd2 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-2' });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [gAnd1, gAnd2] });
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      regroupRules({
        rulesets: [ruleset],
        rulesetApiName: 'r1',
        groupOrApiName: 'g-or-1',
        groupAndApiName: 'g-and-2',
        ruleCombinator: ERuleCombinator.Or,
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated[0].groupsOr).toHaveLength(2);
      expect(updated[0].groupsOr[0].groupsAnd[0].apiName).toBe('g-and-1');
      expect(updated[0].groupsOr[1].groupsAnd[0].apiName).toBe('g-and-2');
    });

    it('should merge OR group into previous group when using ERuleCombinator.And', () => {
      const gAnd1 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const gAnd2 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-2' });
      const groupOr1 = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [gAnd1] });
      const groupOr2 = makeFieldsetRuleGroupOr({ apiName: 'g-or-2', groupsAnd: [gAnd2] });
      const ruleset = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr1, groupOr2] });

      regroupRules({
        rulesets: [ruleset],
        rulesetApiName: 'r1',
        groupOrApiName: 'g-or-2',
        groupAndApiName: 'g-and-2',
        ruleCombinator: ERuleCombinator.And,
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];

      expect(updated[0].groupsOr).toHaveLength(1);
      expect(updated[0].groupsOr[0].groupsAnd).toHaveLength(2);
    });
  });

  describe('getRuleCombinator & getFieldsTooltipText', () => {
    it('should return Or for index 0 and And for index > 0', () => {
      expect(getRuleCombinator(0)).toBe(ERuleCombinator.Or);
      expect(getRuleCombinator(1)).toBe(ERuleCombinator.And);
    });

    it('should return appropriate tooltip message depending on field availability', () => {
      const formatMsgMock = jest.fn(({ id }: { id: string }) => `translated:${id}`);

      expect(getFieldsTooltipText(false, true, formatMsgMock)).toBe('translated:fieldsets.rule-fields-disabled-tooltip');
      expect(getFieldsTooltipText(true, false, formatMsgMock)).toBe('translated:fieldsets.rule-fields-no-number-fields-tooltip');
      expect(getFieldsTooltipText(true, true, formatMsgMock)).toBe('');
    });
  });
});

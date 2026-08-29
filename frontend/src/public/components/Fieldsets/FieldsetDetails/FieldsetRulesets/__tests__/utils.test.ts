import {
  addRuleset,
  addGroupAndToRulesets,
  getNormalizedRulesetOrders,
  updateRuleInRulesets,
  updateRulesetMessage,
  updateRulesetFields,
  deleteRuleset,
  deleteRuleFromRulesets,
  removeFieldFromRuleset,
  regroupRulesInRulesets,
  getRuleCombinator,
  getFieldsTooltipText,
  getFilteredFieldsetRulesets,
} from '../utils';
import { ERuleCombinator, EFieldsetNumberRulesetOperator, IFieldsetRuleSet } from '../../../../../types/fieldset';
import {
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
} from '../../../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';

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
    });
  });

  describe('addGroupAndToRulesets', () => {
    it('should map over rulesets and apply addRule to targeted ruleset', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1' });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      addGroupAndToRulesets({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].groupsOr[0].groupsAnd.length).toBeGreaterThan(r1.groupsOr[0].groupsAnd.length);
      expect(updated[1]).toEqual(r2);
    });

    it('should do nothing when ruleset is not found by apiName', () => {
      const ruleset = makeFieldsetRuleset({ apiName: 'r1' });

      addGroupAndToRulesets({
        rulesets: [ruleset],
        rulesetApiName: 'non-existent',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).not.toHaveBeenCalled();
    });
  });

  describe('updateRuleInRulesets', () => {
    it('should map over rulesets and update matching rule in targeted ruleset', () => {
      const groupAnd = makeFieldsetRuleGroupAnd({
        apiName: 'g-and-1',
        operator: EFieldsetNumberRulesetOperator.SumEqual,
        value: '10',
      });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd] });
      const r1 = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      updateRuleInRulesets({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        ruleGroupOrApiName: 'g-or-1',
        ruleGroupAndApiName: 'g-and-1',
        ruleChanges: {
          value: '50',
        },
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].groupsOr[0].groupsAnd[0].value).toBe('50');
      expect(updated[1]).toEqual(r2);
    });
  });

  describe('updateRulesetMessage', () => {
    it('should update custom error message for targeted ruleset', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', message: 'Old' });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      updateRulesetMessage({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        message: 'New message',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].message).toBe('New message');
      expect(updated[1]).toEqual(r2);
    });
  });

  describe('updateRulesetFields', () => {
    it('should filter non-string values and update fields in targeted ruleset', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', fields: [] });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      updateRulesetFields({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        fieldApiNames: ['field-1', null, 123, 'field-2'],
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].fields).toEqual(['field-1', 'field-2']);
      expect(updated[1]).toEqual(r2);
    });
  });

  describe('deleteRuleset & deleteRuleFromRulesets', () => {
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

    it('should remove target rule from targeted ruleset and keep other rulesets untouched', () => {
      const groupAnd = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd] });
      const r1 = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      deleteRuleFromRulesets({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        ruleGroupOrApiName: 'g-or-1',
        ruleGroupAndApiName: 'g-and-1',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].groupsOr).toHaveLength(0);
      expect(updated[1]).toEqual(r2);
    });

    it('should remove targeted field from fields array in targeted ruleset', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', fields: ['f1', 'f2'] });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      removeFieldFromRuleset({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        fieldApiName: 'f1',
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].fields).toEqual(['f2']);
      expect(updated[1]).toEqual(r2);
    });
  });

  describe('regroupRulesInRulesets', () => {
    it('should regroup rules in targeted ruleset while preserving other rulesets', () => {
      const gAnd1 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const gAnd2 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-2' });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [gAnd1, gAnd2] });
      const r1 = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });
      const r2 = makeFieldsetRuleset({ apiName: 'r2' });

      regroupRulesInRulesets({
        rulesets: [r1, r2],
        rulesetApiName: 'r1',
        groupOrApiName: 'g-or-1',
        groupAndApiName: 'g-and-2',
        ruleCombinator: ERuleCombinator.Or,
        onRulesetsChange: onRulesetsChangeMock,
      });

      expect(onRulesetsChangeMock).toHaveBeenCalledTimes(1);
      const updated: IFieldsetRuleSet[] = onRulesetsChangeMock.mock.calls[0][0];
      expect(updated[0].groupsOr).toHaveLength(2);
      expect(updated[1]).toEqual(r2);
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

  describe('getFilteredFieldsetRulesets', () => {
    it('removes rulesets whose fields no longer exist', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', fields: ['f1'], order: 0 });
      const r2 = makeFieldsetRuleset({ apiName: 'r2', fields: ['f2'], order: 1 });
      const existingFields = [makeExtraField({ apiName: 'f1' })];

      const result = getFilteredFieldsetRulesets([r1, r2], existingFields);

      expect(result).toHaveLength(1);
      expect(result[0].apiName).toBe('r1');
      expect(result[0].order).toBe(0);
    });

    it('keeps ruleset if at least one field still exists', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', fields: ['f1', 'f2'] });
      const existingFields = [makeExtraField({ apiName: 'f1' })];

      const result = getFilteredFieldsetRulesets([r1], existingFields);

      expect(result).toHaveLength(1);
    });

    it('returns same reference when no rulesets are removed', () => {
      const rulesets = [makeFieldsetRuleset({ apiName: 'r1', fields: ['f1'] })];
      const existingFields = [makeExtraField({ apiName: 'f1' })];

      const result = getFilteredFieldsetRulesets(rulesets, existingFields);

      expect(result).toBe(rulesets);
    });

    it('removes all rulesets when no fields exist', () => {
      const r1 = makeFieldsetRuleset({ apiName: 'r1', fields: ['f1'] });

      const result = getFilteredFieldsetRulesets([r1], []);

      expect(result).toHaveLength(0);
    });
  });
});

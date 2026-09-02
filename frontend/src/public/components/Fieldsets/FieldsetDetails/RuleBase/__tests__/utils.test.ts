import {
  traverseGroupsAnd,
  updateRule,
  deleteRule,
  addRule,
  regroupRules,
  getRuleCombinator,
  getFieldRuleShowOperators,
} from '../utils';
import { ERuleCombinator, EFieldsetNumberRulesetOperator, IFieldsetRuleGroupAnd } from '../../../../../types/fieldset';
import { EExtraFieldType } from '../../../../../types/template';
import {
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
} from '../../../../../__stubs__/fieldsets.factory';

describe('RuleBase utils', () => {
  const createEmptyGroupAnd = (): IFieldsetRuleGroupAnd => ({
    apiName: 'new-g-and',
    operator: EFieldsetNumberRulesetOperator.SumEqual,
    value: '',
  });

  describe('traverseGroupsAnd', () => {
    it('should apply changeRules callback to targeted groupOr and filter out empty groupsOr', () => {
      const groupAnd1 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const groupAnd2 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-2' });
      const groupOr1 = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd1] });
      const groupOr2 = makeFieldsetRuleGroupOr({ apiName: 'g-or-2', groupsAnd: [groupAnd2] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr1, groupOr2] });

      const updated = traverseGroupsAnd(ruleSet, 'g-or-1', () => []);

      expect(updated.groupsOr).toHaveLength(1);
      expect(updated.groupsOr[0].apiName).toBe('g-or-2');
    });
  });

  describe('updateRule', () => {
    it('should update properties of the matching rule in targeted groupOr', () => {
      const groupAnd = makeFieldsetRuleGroupAnd({
        apiName: 'g-and-1',
        operator: EFieldsetNumberRulesetOperator.SumEqual,
        value: '10',
      });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      const updated = updateRule(ruleSet, 'g-or-1', 'g-and-1', {
        operator: EFieldsetNumberRulesetOperator.SumGreaterThan,
        value: '50',
      } as Partial<IFieldsetRuleGroupAnd>);

      const target = updated.groupsOr[0].groupsAnd[0];
      expect(target.operator).toBe(EFieldsetNumberRulesetOperator.SumGreaterThan);
      expect(target.value).toBe('50');
    });
  });

  describe('deleteRule', () => {
    it('should remove rule by apiName and remove empty groupOr if no rules left', () => {
      const groupAnd = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [groupAnd] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      const updated = deleteRule(ruleSet, 'g-or-1', 'g-and-1');

      expect(updated.groupsOr).toHaveLength(0);
    });
  });

  describe('addRule', () => {
    it('should add a new rule to targeted groupOr when groupOrApiName is provided', () => {
      const groupOr1 = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [] });
      const groupOr2 = makeFieldsetRuleGroupOr({ apiName: 'g-or-2', groupsAnd: [] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr1, groupOr2] });

      const updated = addRule(ruleSet, createEmptyGroupAnd, 'g-or-1');

      expect(updated.groupsOr[0].groupsAnd).toHaveLength(1);
      expect(updated.groupsOr[0].groupsAnd[0].apiName).toBe('new-g-and');
    });

    it('should add a new rule to the last groupOr when groupOrApiName is omitted', () => {
      const groupOr1 = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [makeFieldsetRuleGroupAnd()] });
      const groupOr2 = makeFieldsetRuleGroupOr({ apiName: 'g-or-2', groupsAnd: [makeFieldsetRuleGroupAnd()] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr1, groupOr2] });

      const updated = addRule(ruleSet, createEmptyGroupAnd);

      expect(updated.groupsOr[0].groupsAnd).toHaveLength(1);
      expect(updated.groupsOr[1].groupsAnd).toHaveLength(2);
    });

    it('should create a new groupOr if groupsOr is empty', () => {
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [] });

      const updated = addRule(ruleSet, createEmptyGroupAnd);

      expect(updated.groupsOr).toHaveLength(1);
      expect(updated.groupsOr[0].groupsAnd).toHaveLength(1);
    });
  });

  describe('regroupRules', () => {
    it('should split rules into a new OR group when ruleCombinator is Or', () => {
      const gAnd1 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const gAnd2 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-2' });
      const groupOr = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [gAnd1, gAnd2] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr] });

      const updated = regroupRules(ruleSet, 'g-or-1', 'g-and-2', ERuleCombinator.Or);

      expect(updated.groupsOr).toHaveLength(2);
      expect(updated.groupsOr[0].groupsAnd[0].apiName).toBe('g-and-1');
      expect(updated.groupsOr[1].groupsAnd[0].apiName).toBe('g-and-2');
    });

    it('should merge OR group into previous group when ruleCombinator is And', () => {
      const gAnd1 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-1' });
      const gAnd2 = makeFieldsetRuleGroupAnd({ apiName: 'g-and-2' });
      const groupOr1 = makeFieldsetRuleGroupOr({ apiName: 'g-or-1', groupsAnd: [gAnd1] });
      const groupOr2 = makeFieldsetRuleGroupOr({ apiName: 'g-or-2', groupsAnd: [gAnd2] });
      const ruleSet = makeFieldsetRuleset({ apiName: 'r1', groupsOr: [groupOr1, groupOr2] });

      const updated = regroupRules(ruleSet, 'g-or-2', 'g-and-2', ERuleCombinator.And);

      expect(updated.groupsOr).toHaveLength(1);
      expect(updated.groupsOr[0].groupsAnd).toHaveLength(2);
    });
  });

  describe('getRuleCombinator', () => {
    it('should return Or for index 0 and And for index > 0', () => {
      expect(getRuleCombinator(0)).toBe(ERuleCombinator.Or);
      expect(getRuleCombinator(1)).toBe(ERuleCombinator.And);
    });
  });

  describe('getFieldRuleShowOperators', () => {
    it('returns list of operators with localized labels for specified field type', () => {
      const messages = {
        'templates.conditions.equal': 'Equal',
        'templates.conditions.not-equals': 'Not equal',
      };

      const result = getFieldRuleShowOperators(EExtraFieldType.Text, messages);

      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toHaveProperty('apiName');
      expect(result[0]).toHaveProperty('name');
    });
  });
});

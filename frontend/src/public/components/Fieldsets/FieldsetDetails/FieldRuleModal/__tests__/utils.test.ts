import {
  createEmptyFieldRule,
  createEmptyFieldRuleGroupOr,
  createEmptyFieldRuleSet,
  isFieldRulesetValid,
} from '../utils';

import {
  EFieldRuleType,
  EFieldRuleValidatorOperator,
  IFieldRuleSet,
} from '../../../../../types/fieldset';

import { EExtraFieldType } from '../../../../../types/template';
import { TRuleFieldOption } from '../../RuleBase/types';

const makeValidRuleset = (overrides: Partial<IFieldRuleSet> = {}): IFieldRuleSet => ({
  apiName: 'rs-1',
  name: 'Test Rule',
  type: EFieldRuleType.Validator,
  message: null,
  order: 0,
  groupsOr: [
    {
      apiName: 'or-1',
      groupsAnd: [
        {
          apiName: 'and-1',
          field: null,
          operator: EFieldRuleValidatorOperator.Equal,
          value: '100',
        },
      ],
    },
  ],
  ...overrides,
});

const makeFieldOptions = (overrides: Partial<TRuleFieldOption> = {}): TRuleFieldOption[] => [
  { apiName: 'field_1', name: 'Field 1', type: EExtraFieldType.Text, ...overrides },
];

describe('FieldRuleModal utils', () => {
  describe('createEmptyFieldRule', () => {
    it('creates a rule with operator Equal for Validator type', () => {
      const rule = createEmptyFieldRule(EFieldRuleType.Validator);

      expect(rule.apiName).toBeTruthy();
      expect(rule.operator).toBe(EFieldRuleValidatorOperator.Equal);
      expect(rule.field).toBeNull();
      expect(rule.value).toBe('');
    });

    it('creates a rule with operator null for Show type', () => {
      const rule = createEmptyFieldRule(EFieldRuleType.Show);

      expect(rule.operator).toBeNull();
      expect(rule.field).toBeNull();
    });
  });

  describe('createEmptyFieldRuleGroupOr', () => {
    it('creates an OR group with a single empty rule inside', () => {
      const groupOr = createEmptyFieldRuleGroupOr();

      expect(groupOr.apiName).toBeTruthy();
      expect(groupOr.groupsAnd).toHaveLength(1);
    });
  });

  describe('createEmptyFieldRuleSet', () => {
    it('creates a Validator ruleset with empty string message', () => {
      const ruleSet = createEmptyFieldRuleSet(EFieldRuleType.Validator);

      expect(ruleSet.type).toBe(EFieldRuleType.Validator);
      expect(ruleSet.message).toBe('');
      expect(ruleSet.name).toBe('');
      expect(ruleSet.groupsOr).toHaveLength(1);
    });

    it('creates a Show ruleset with null message', () => {
      const ruleSet = createEmptyFieldRuleSet(EFieldRuleType.Show);

      expect(ruleSet.type).toBe(EFieldRuleType.Show);
      expect(ruleSet.message).toBeNull();
    });
  });

  describe('isFieldRulesetValid', () => {
    it('returns false when name is empty', () => {
      const ruleset = makeValidRuleset({ name: '' });

      expect(isFieldRulesetValid(ruleset)).toBe(false);
    });

    it('returns false when name contains only whitespace', () => {
      const ruleset = makeValidRuleset({ name: '   ' });

      expect(isFieldRulesetValid(ruleset)).toBe(false);
    });

    it('returns false when there are no rules', () => {
      const ruleset = makeValidRuleset({
        groupsOr: [{ apiName: 'or-1', groupsAnd: [] }],
      });

      expect(isFieldRulesetValid(ruleset)).toBe(false);
    });

    it('returns false when validator rule has empty value', () => {
      const ruleset = makeValidRuleset({
        type: EFieldRuleType.Validator,
        groupsOr: [{
          apiName: 'or-1',
          groupsAnd: [{
            apiName: 'and-1',
            field: null,
            operator: EFieldRuleValidatorOperator.Equal,
            value: '',
          }],
        }],
      });

      expect(isFieldRulesetValid(ruleset)).toBe(false);
    });

    it('returns true when validator rule has a filled value', () => {
      const ruleset = makeValidRuleset({
        type: EFieldRuleType.Validator,
      });

      expect(isFieldRulesetValid(ruleset)).toBe(true);
    });

    it('returns false when show rule has no field selected', () => {
      const ruleset = makeValidRuleset({
        type: EFieldRuleType.Show,
        groupsOr: [{
          apiName: 'or-1',
          groupsAnd: [{
            apiName: 'and-1',
            field: null,
            operator: EFieldRuleValidatorOperator.Equal,
            value: 'test',
          }],
        }],
      });

      expect(isFieldRulesetValid(ruleset, makeFieldOptions())).toBe(false);
    });

    it('returns false when show rule has empty value for a non-File field', () => {
      const ruleset = makeValidRuleset({
        type: EFieldRuleType.Show,
        groupsOr: [{
          apiName: 'or-1',
          groupsAnd: [{
            apiName: 'and-1',
            field: 'field_1',
            operator: EFieldRuleValidatorOperator.Equal,
            value: '',
          }],
        }],
      });

      expect(isFieldRulesetValid(ruleset, makeFieldOptions())).toBe(false);
    });

    it('returns true when show rule has empty value for a File field', () => {
      const ruleset = makeValidRuleset({
        type: EFieldRuleType.Show,
        groupsOr: [{
          apiName: 'or-1',
          groupsAnd: [{
            apiName: 'and-1',
            field: 'field_1',
            operator: EFieldRuleValidatorOperator.Equal,
            value: '',
          }],
        }],
      });

      const fileFieldOptions = makeFieldOptions({ type: EExtraFieldType.File });

      expect(isFieldRulesetValid(ruleset, fileFieldOptions)).toBe(true);
    });
  });
});

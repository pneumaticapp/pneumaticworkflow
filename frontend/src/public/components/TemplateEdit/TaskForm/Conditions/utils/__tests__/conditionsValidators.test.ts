import { getConditionRuleErrorId } from '../conditionsValidators';
import { EConditionLogicOperations, EConditionOperators, TConditionRule } from '../../types';
import { EExtraFieldType } from '../../../../../../types/template';

const makeRule = (overrides: Partial<TConditionRule> = {}): TConditionRule =>
  ({
    ruleApiName: 'rule-1',
    predicateApiName: 'predicate-1',
    logicOperation: EConditionLogicOperations.And,
    field: 'field-1',
    fieldType: EExtraFieldType.String,
    operator: EConditionOperators.Equal,
    value: 'text',
    ...overrides,
  }) as TConditionRule;

describe('getConditionRuleErrorId', () => {
  it('ignores a rule without a selected field', () => {
    expect(getConditionRuleErrorId(makeRule({ field: null, operator: null }))).toBe('');
  });

  it('reports a rule without an operator', () => {
    expect(getConditionRuleErrorId(makeRule({ operator: null }))).toBe('validation.condition-incomplete');
  });

  it('reports a missing value for an operator that needs one', () => {
    expect(getConditionRuleErrorId(makeRule({ value: '' }))).toBe('validation.condition-incomplete');
  });

  it('accepts an operator without a value', () => {
    expect(getConditionRuleErrorId(makeRule({ operator: EConditionOperators.Exist, value: null }))).toBe('');
  });

  it('reports an invalid number', () => {
    const rule = makeRule({ fieldType: EExtraFieldType.Number, value: 'abc' as unknown as number });

    expect(getConditionRuleErrorId(rule)).toBe('validation.number-invalid-format');
  });
});

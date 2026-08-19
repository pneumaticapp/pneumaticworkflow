import {
  FIELDSET_RULES_MSG_FIELDS_NUMBER,
  FIELDSET_RULES_MSG_FIELDS_REQUIRED,
  FIELDSET_RULES_MSG_INCOMPLETE,
  FIELDSET_RULES_MSG_VALUE_NUMBER,
  FIELDSET_RULES_MSG_VALUE_REQUIRED,
} from '../constants';
import { validateFieldsetRules } from '../validators';
import { EFieldsetNumberRulesetOperator } from '../../../types/fieldset';
import { EExtraFieldType } from '../../../types/template';
import { makeFieldsetRuleset } from '../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../__stubs__/fields.factory';

const numberField = () => makeExtraField({ apiName: 'f1', type: EExtraFieldType.Number });
const stringField = () => makeExtraField({ apiName: 'f2', type: EExtraFieldType.String });

describe('validateFieldsetRules', () => {
  it('returns empty string for an empty rules list', () => {
    expect(validateFieldsetRules([])).toBe('');
  });

  it('returns incomplete when rule has empty value and fields', () => {
    expect(
      validateFieldsetRules([
        makeFieldsetRuleset({
          fields: [],
          groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '' }] }],
        }),
      ]),
    ).toBe(FIELDSET_RULES_MSG_INCOMPLETE);
  });

  it('returns value-required when value is empty but fields are selected', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '' }] }],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_REQUIRED);
  });

  it('returns value-number when value is not numeric for sum_equal', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: 'abc' }] }],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_NUMBER);
  });

  it('returns fields-required when fields are empty but value is numeric', () => {
    expect(
      validateFieldsetRules([
        makeFieldsetRuleset({
          fields: [],
          groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '100' }] }],
        }),
      ]),
    ).toBe(FIELDSET_RULES_MSG_FIELDS_REQUIRED);
  });

  it('returns fields-number when selected fields include a non-number field', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f2'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '100' }] }],
          }),
        ],
        [stringField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_FIELDS_NUMBER);
  });

  it('returns empty string when value is numeric and all fields are number', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '100' }] }],
          }),
        ],
        [numberField()],
      ),
    ).toBe('');
  });

  it('treats whitespace-only value as empty (trim)', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '   ' }] }],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_REQUIRED);
  });

  it('returns fields-number when field apiName is missing from availableFields', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['missing'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '100' }] }],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_FIELDS_NUMBER);
  });

  it('returns the first broken rule error in list order', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [{ apiName: 'g-or-1', groupsAnd: [{ apiName: 'g-and-1', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '100' }] }],
          }),
          makeFieldsetRuleset({
            fields: [],
            groupsOr: [{ apiName: 'g-or-2', groupsAnd: [{ apiName: 'g-and-2', operator: EFieldsetNumberRulesetOperator.SumEqual, value: '' }] }],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_INCOMPLETE);
  });
});

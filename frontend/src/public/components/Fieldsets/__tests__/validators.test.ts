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
import { makeFieldsetRuleset, makeFieldsetRuleGroupOr, makeFieldsetRuleGroupAnd } from '../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../__stubs__/fields.factory';

const numberField = (apiName = 'f1') => makeExtraField({ apiName, type: EExtraFieldType.Number });
const stringField = (apiName = 'f2') => makeExtraField({ apiName, type: EExtraFieldType.String });

describe('validateFieldsetRules', () => {
  it('returns empty string for an empty rules list', () => {
    expect(validateFieldsetRules([])).toBe('');
  });

  it('returns incomplete when rule has empty groupsOr and empty fields', () => {
    expect(
      validateFieldsetRules([
        makeFieldsetRuleset({
          fields: [],
          groupsOr: [],
        }),
      ]),
    ).toBe(FIELDSET_RULES_MSG_INCOMPLETE);
  });

  it('returns value-required when groupsOr is empty but fields are selected', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_REQUIRED);
  });

  it('returns value-required when value is empty but fields are selected', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [
              makeFieldsetRuleGroupOr({
                groupsAnd: [makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumEqual, value: '' })],
              }),
            ],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_REQUIRED);
  });

  describe('operator validations & numeric values', () => {
    const operators = [
      EFieldsetNumberRulesetOperator.SumEqual,
      EFieldsetNumberRulesetOperator.SumGreaterThan,
      EFieldsetNumberRulesetOperator.SumLessThan,
    ];

    operators.forEach((operator) => {
      it(`accepts valid integer, decimal, and negative numbers for operator ${operator}`, () => {
        ['100', '99.95', '-42', '0'].forEach((val) => {
          expect(
            validateFieldsetRules(
              [
                makeFieldsetRuleset({
                  fields: ['f1'],
                  groupsOr: [
                    makeFieldsetRuleGroupOr({
                      groupsAnd: [makeFieldsetRuleGroupAnd({ operator, value: val })],
                    }),
                  ],
                }),
              ],
              [numberField()],
            ),
          ).toBe('');
        });
      });

      it(`returns value-number for invalid numeric strings for operator ${operator}`, () => {
        ['abc', '12a', '10.5.2', '++50'].forEach((val) => {
          expect(
            validateFieldsetRules(
              [
                makeFieldsetRuleset({
                  fields: ['f1'],
                  groupsOr: [
                    makeFieldsetRuleGroupOr({
                      groupsAnd: [makeFieldsetRuleGroupAnd({ operator, value: val })],
                    }),
                  ],
                }),
              ],
              [numberField()],
            ),
          ).toBe(FIELDSET_RULES_MSG_VALUE_NUMBER);
        });
      });
    });
  });

  it('returns fields-required when fields are empty but value is numeric', () => {
    expect(
      validateFieldsetRules([
        makeFieldsetRuleset({
          fields: [],
          groupsOr: [
            makeFieldsetRuleGroupOr({
              groupsAnd: [makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumGreaterThan, value: '100' })],
            }),
          ],
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
            groupsOr: [
              makeFieldsetRuleGroupOr({
                groupsAnd: [makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumLessThan, value: '100' })],
              }),
            ],
          }),
        ],
        [stringField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_FIELDS_NUMBER);
  });

  it('treats whitespace-only value as empty (trim)', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1'],
            groupsOr: [
              makeFieldsetRuleGroupOr({
                groupsAnd: [makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumEqual, value: '   ' })],
              }),
            ],
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
            groupsOr: [
              makeFieldsetRuleGroupOr({
                groupsAnd: [makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumEqual, value: '100' })],
              }),
            ],
          }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_FIELDS_NUMBER);
  });

  it('validates multiple nested AND/OR rules and returns the first failing error', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1', 'f3'],
            groupsOr: [
              makeFieldsetRuleGroupOr({
                groupsAnd: [
                  makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumGreaterThan, value: '10' }),
                  makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumLessThan, value: 'invalid' }),
                ],
              }),
            ],
          }),
        ],
        [numberField('f1'), numberField('f3')],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_NUMBER);
  });

  it('returns empty string when multiple nested AND/OR rules with multiple number fields are valid', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetRuleset({
            fields: ['f1', 'f3'],
            groupsOr: [
              makeFieldsetRuleGroupOr({
                groupsAnd: [
                  makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumGreaterThan, value: '10' }),
                  makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumLessThan, value: '500' }),
                ],
              }),
              makeFieldsetRuleGroupOr({
                groupsAnd: [
                  makeFieldsetRuleGroupAnd({ operator: EFieldsetNumberRulesetOperator.SumEqual, value: '250' }),
                ],
              }),
            ],
          }),
        ],
        [numberField('f1'), numberField('f3')],
      ),
    ).toBe('');
  });
});

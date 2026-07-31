import {
  FIELDSET_RULES_MSG_FIELDS_NUMBER,
  FIELDSET_RULES_MSG_FIELDS_REQUIRED,
  FIELDSET_RULES_MSG_INCOMPLETE,
  FIELDSET_RULES_MSG_VALUE_NUMBER,
  FIELDSET_RULES_MSG_VALUE_REQUIRED,
} from '../constants';
import { validateFieldsetRules } from '../validators';
import { EFieldsetRuleType } from '../../../types/fieldset';
import { EExtraFieldType } from '../../../types/template';
import { makeFieldsetTemplateRule } from '../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../__stubs__/fields.factory';

const numberField = () => makeExtraField({ apiName: 'f1', type: EExtraFieldType.Number });
const stringField = () => makeExtraField({ apiName: 'f2', type: EExtraFieldType.String });

describe('validateFieldsetRules', () => {
  it('returns empty string for an empty rules list', () => {
    expect(validateFieldsetRules([])).toBe('');
  });

  it('returns incomplete when rule has empty value and fields', () => {
    expect(validateFieldsetRules([makeFieldsetTemplateRule({ apiName: 'r1', value: '', fields: [] })])).toBe(
      FIELDSET_RULES_MSG_INCOMPLETE,
    );
  });

  it('returns value-required when value is empty but fields are selected', () => {
    expect(
      validateFieldsetRules([makeFieldsetTemplateRule({ apiName: 'r1', value: '', fields: ['f1'] })], [numberField()]),
    ).toBe(FIELDSET_RULES_MSG_VALUE_REQUIRED);
  });

  it('returns value-number when value is not numeric for sum_equal', () => {
    expect(
      validateFieldsetRules(
        [makeFieldsetTemplateRule({ apiName: 'r1', value: 'abc', fields: ['f1'] })],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_NUMBER);
  });

  it('returns fields-required when fields are empty but value is numeric', () => {
    expect(validateFieldsetRules([makeFieldsetTemplateRule({ apiName: 'r1', value: '100', fields: [] })])).toBe(
      FIELDSET_RULES_MSG_FIELDS_REQUIRED,
    );
  });

  it('returns fields-number when selected fields include a non-number field', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetTemplateRule({
            apiName: 'r1',
            type: EFieldsetRuleType.SumEqual,
            value: '100',
            fields: ['f2'],
          }),
        ],
        [stringField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_FIELDS_NUMBER);
  });

  it('returns empty string when value is numeric and all fields are number', () => {
    expect(
      validateFieldsetRules(
        [makeFieldsetTemplateRule({ apiName: 'r1', value: '100', fields: ['f1'] })],
        [numberField()],
      ),
    ).toBe('');
  });

  it('treats whitespace-only value as empty (trim)', () => {
    expect(
      validateFieldsetRules(
        [makeFieldsetTemplateRule({ apiName: 'r1', value: '   ', fields: ['f1'] })],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_VALUE_REQUIRED);
  });

  it('returns fields-number when field apiName is missing from availableFields', () => {
    expect(
      validateFieldsetRules(
        [
          makeFieldsetTemplateRule({
            apiName: 'r1',
            type: EFieldsetRuleType.SumEqual,
            value: '100',
            fields: ['missing'],
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
          makeFieldsetTemplateRule({ apiName: 'r1', value: '100', fields: ['f1'] }),
          makeFieldsetTemplateRule({ apiName: 'r2', value: '', fields: [] }),
        ],
        [numberField()],
      ),
    ).toBe(FIELDSET_RULES_MSG_INCOMPLETE);
  });
});

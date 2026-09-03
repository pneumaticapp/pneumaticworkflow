import { EFieldRuleType } from '../../../../types/fieldset';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldRuleSet, makeFieldRuleGroupOr, makeFieldRuleGroupAnd } from '../../../../__stubs__/fieldsets.factory';
import { getFieldsWithFilteredRulesets } from '../utils';

describe('getFieldsWithFilteredRulesets', () => {
  it('removes show ruleset that references the deleted field', () => {
    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [
        makeFieldRuleSet({
          type: EFieldRuleType.Show,
          groupsOr: [makeFieldRuleGroupOr({
            groupsAnd: [makeFieldRuleGroupAnd({ field: 'field_b' })],
          })],
        }),
      ],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(0);
  });

  it('keeps show ruleset that references a different field', () => {
    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [
        makeFieldRuleSet({
          type: EFieldRuleType.Show,
          groupsOr: [makeFieldRuleGroupOr({
            groupsAnd: [makeFieldRuleGroupAnd({ field: 'field_c' })],
          })],
        }),
      ],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(1);
  });

  it('does not remove validator rulesets', () => {
    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [makeFieldRuleSet({ type: EFieldRuleType.Validator })],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(1);
  });

  it('returns field unchanged when it has no rulesets', () => {
    const fieldA = makeExtraField({ apiName: 'field_a' });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0]).toBe(fieldA);
  });

  it('removes show ruleset and keeps validator ruleset on the same field', () => {
    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [makeFieldRuleGroupOr({
        groupsAnd: [makeFieldRuleGroupAnd({ field: 'field_b' })],
      })],
    });
    const validatorRuleset = makeFieldRuleSet({ type: EFieldRuleType.Validator });

    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [showRuleset, validatorRuleset],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(1);
    expect(result[0].rulesets).toEqual([validatorRuleset]);
  });
});

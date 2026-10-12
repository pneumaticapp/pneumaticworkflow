import {
  checkDependentFieldValue,
  isFieldHidden,
  updateFieldsHidden,
  getVisibleFields,
  getVisibleFieldsByShowRules,
} from '../fieldShowVisibility';
import { EFieldRuleOperator, EFieldRuleType, IFieldRuleGroupOr, IFieldRuleSet } from '../../types/fieldset';
import { EExtraFieldType, IExtraField } from '../../types/template';
import { makeExtraField } from '../../__stubs__/fields.factory';
import {
  makeFieldRuleShowGroupAnd,
  makeFieldRuleGroupOr,
  makeFieldRuleSet,
  makeFieldsetRuntime,
} from '../../__stubs__/fieldsets.factory';

describe('checkDependentFieldValue: conditions for individual operators', () => {
  describe('exist and not_exist operators', () => {
    it('correctly checks string fields for presence of value', () => {
      const fieldWithValue = makeExtraField({ value: 'text' });
      const fieldWithEmptySpaces = makeExtraField({ value: '   ' });
      const fieldWithNull = makeExtraField({ value: null });

      expect(checkDependentFieldValue(fieldWithValue, EFieldRuleOperator.Exist, '')).toBe(true);
      expect(checkDependentFieldValue(fieldWithEmptySpaces, EFieldRuleOperator.Exist, '')).toBe(false);
      expect(checkDependentFieldValue(fieldWithNull, EFieldRuleOperator.Exist, '')).toBe(false);

      expect(checkDependentFieldValue(fieldWithValue, EFieldRuleOperator.NotExist, '')).toBe(false);
      expect(checkDependentFieldValue(fieldWithEmptySpaces, EFieldRuleOperator.NotExist, '')).toBe(true);
    });

    it('correctly checks array fields for presence of value', () => {
      const fieldWithItems = makeExtraField({ value: ['option 1', 'option 2'] });
      const fieldEmptyArray = makeExtraField({ value: [] });

      expect(checkDependentFieldValue(fieldWithItems, EFieldRuleOperator.Exist, '')).toBe(true);
      expect(checkDependentFieldValue(fieldEmptyArray, EFieldRuleOperator.Exist, '')).toBe(false);
      expect(checkDependentFieldValue(fieldEmptyArray, EFieldRuleOperator.NotExist, '')).toBe(true);
    });

    it('correctly checks file fields for presence of attachments', () => {
      const fieldWithAttachments = makeExtraField({
        type: EExtraFieldType.File,
        attachments: [{ id: 'file-1', name: 'document.pdf', url: 'https://example.com/file', size: 1024 }],
      });
      const fieldWithoutAttachments = makeExtraField({
        type: EExtraFieldType.File,
        attachments: [],
        value: '',
      });

      expect(checkDependentFieldValue(fieldWithAttachments, EFieldRuleOperator.Exist, '')).toBe(true);
      expect(checkDependentFieldValue(fieldWithoutAttachments, EFieldRuleOperator.Exist, '')).toBe(false);
    });
  });

  describe('equal and not_equal operators', () => {
    it('compares numeric values', () => {
      const numberField = makeExtraField({ value: '100' });

      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.Equal, '100')).toBe(true);
      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.Equal, '99')).toBe(false);
      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.NotEqual, '99')).toBe(true);
    });

    it('compares string values', () => {
      const stringField = makeExtraField({ value: 'in_progress' });

      expect(checkDependentFieldValue(stringField, EFieldRuleOperator.Equal, 'in_progress')).toBe(true);
      expect(checkDependentFieldValue(stringField, EFieldRuleOperator.Equal, 'completed')).toBe(false);
      expect(checkDependentFieldValue(stringField, EFieldRuleOperator.NotEqual, 'completed')).toBe(true);
    });

    it('returns false when field value is empty or null', () => {
      const emptyField = makeExtraField({ value: null });

      expect(checkDependentFieldValue(emptyField, EFieldRuleOperator.Equal, 'value')).toBe(false);
      expect(checkDependentFieldValue(emptyField, EFieldRuleOperator.NotEqual, 'value')).toBe(true);
    });
  });

  describe('contain and not_contain operators', () => {
    it('checks substring in string fields', () => {
      const stringField = makeExtraField({ value: 'document package received' });

      expect(checkDependentFieldValue(stringField, EFieldRuleOperator.Contain, 'package')).toBe(true);
      expect(checkDependentFieldValue(stringField, EFieldRuleOperator.Contain, 'rejected')).toBe(false);
      expect(checkDependentFieldValue(stringField, EFieldRuleOperator.NotContain, 'rejected')).toBe(true);
    });

    it('checks element presence in array', () => {
      const arrayField = makeExtraField({ value: ['red', 'green', 'blue'] });

      expect(checkDependentFieldValue(arrayField, EFieldRuleOperator.Contain, 'green')).toBe(true);
      expect(checkDependentFieldValue(arrayField, EFieldRuleOperator.Contain, 'yellow')).toBe(false);
      expect(checkDependentFieldValue(arrayField, EFieldRuleOperator.NotContain, 'yellow')).toBe(true);
    });

    it('returns false for contain when field value is null or undefined', () => {
      const nullField = makeExtraField({ value: null });
      const undefinedField = makeExtraField({ value: undefined });

      expect(checkDependentFieldValue(nullField, EFieldRuleOperator.Contain, 'null')).toBe(false);
      expect(checkDependentFieldValue(undefinedField, EFieldRuleOperator.Contain, 'undefined')).toBe(false);
      expect(checkDependentFieldValue(nullField, EFieldRuleOperator.NotContain, 'text')).toBe(true);
    });
  });

  describe('greater_than and less_than operators', () => {
    it('correctly compares numeric values', () => {
      const numberField = makeExtraField({ type: EExtraFieldType.Number, value: '25' });

      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.GreaterThan, '20')).toBe(true);
      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.GreaterThan, '25')).toBe(false);
      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.GreaterThan, '30')).toBe(false);

      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.LessThan, '30')).toBe(true);
      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.LessThan, '25')).toBe(false);
      expect(checkDependentFieldValue(numberField, EFieldRuleOperator.LessThan, '20')).toBe(false);
    });

    it('returns false when numeric field value is empty string', () => {
      const emptyNumberField = makeExtraField({ type: EExtraFieldType.Number, value: '' });

      expect(checkDependentFieldValue(emptyNumberField, EFieldRuleOperator.GreaterThan, '10')).toBe(false);
      expect(checkDependentFieldValue(emptyNumberField, EFieldRuleOperator.LessThan, '10')).toBe(false);
    });

    it('returns false when numeric field value is null or undefined', () => {
      const nullField = makeExtraField({ type: EExtraFieldType.Number, value: null });

      expect(checkDependentFieldValue(nullField, EFieldRuleOperator.GreaterThan, '-5')).toBe(false);
      expect(checkDependentFieldValue(nullField, EFieldRuleOperator.LessThan, '100')).toBe(false);
    });
  });
});

describe('isFieldHidden: determining field visibility considering show rules', () => {
  it('returns field.isHidden when field has no show rulesets', () => {
    const visibleField = makeExtraField({ isHidden: false, rulesets: [] });
    const hiddenField = makeExtraField({ isHidden: true, rulesets: [] });

    expect(isFieldHidden(visibleField, new Map())).toBe(false);
    expect(isFieldHidden(hiddenField, new Map())).toBe(true);
  });

  it('computes field visibility when show rulesets are present', () => {
    const trigger = makeExtraField({ apiName: 'trigger', value: 'yes' });
    const fieldsMap = new Map<string, IExtraField>([['trigger', trigger]]);

    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({ field: 'trigger', operator: EFieldRuleOperator.Equal, value: 'yes' }),
          ],
        }),
      ],
    });

    const controlled = makeExtraField({ apiName: 'controlled', isHidden: true, rulesets: [showRuleset] });

    expect(isFieldHidden(controlled, fieldsMap)).toBe(false);

    trigger.value = 'no';
    expect(isFieldHidden(controlled, fieldsMap)).toBe(true);
  });
});

describe('isFieldHidden: OR(AND(...)) formula evaluation logic', () => {
  it('returns true for ruleset with empty groupsOr', () => {
    const ruleset: IFieldRuleSet = makeFieldRuleSet({ type: EFieldRuleType.Show, groupsOr: [] });
    const field = makeExtraField({ apiName: 'target', rulesets: [ruleset] });
    const fieldsMap = new Map<string, IExtraField>([['target', field]]);
    expect(isFieldHidden(field, fieldsMap)).toBe(true);
  });

  it('requires ALL conditions in a single AND group to be met', () => {
    const fieldA = makeExtraField({ apiName: 'field-a', value: '10', type: EExtraFieldType.Number });
    const fieldB = makeExtraField({ apiName: 'field-b', value: '3', type: EExtraFieldType.Number });

    const andGroup: IFieldRuleGroupOr = makeFieldRuleGroupOr({
      groupsAnd: [
        makeFieldRuleShowGroupAnd({ field: 'field-a', operator: EFieldRuleOperator.Equal, value: '10' }),
        makeFieldRuleShowGroupAnd({ field: 'field-b', operator: EFieldRuleOperator.GreaterThan, value: '5' }),
      ],
    });
    const ruleset: IFieldRuleSet = makeFieldRuleSet({ type: EFieldRuleType.Show, groupsOr: [andGroup] });
    const targetField = makeExtraField({ apiName: 'target', rulesets: [ruleset] });
    const fieldsMap = new Map<string, IExtraField>([
      ['field-a', fieldA],
      ['field-b', fieldB],
      ['target', targetField],
    ]);

    expect(isFieldHidden(targetField, fieldsMap)).toBe(true);

    fieldB.value = '7';
    expect(isFieldHidden(targetField, fieldsMap)).toBe(false);
  });

  it('considers field visible if AT LEAST ONE OR group is met', () => {
    const statusField = makeExtraField({ apiName: 'status', value: 'pending' });

    const orGroup1: IFieldRuleGroupOr = makeFieldRuleGroupOr({
      groupsAnd: [
        makeFieldRuleShowGroupAnd({ field: 'status', operator: EFieldRuleOperator.Equal, value: 'approved' }),
      ],
    });
    const orGroup2: IFieldRuleGroupOr = makeFieldRuleGroupOr({
      groupsAnd: [makeFieldRuleShowGroupAnd({ field: 'status', operator: EFieldRuleOperator.Equal, value: 'pending' })],
    });
    const ruleset: IFieldRuleSet = makeFieldRuleSet({ groupsOr: [orGroup1, orGroup2] });
    const targetField = makeExtraField({ apiName: 'target', rulesets: [ruleset] });
    const fieldsMap = new Map<string, IExtraField>([
      ['status', statusField],
      ['target', targetField],
    ]);

    expect(isFieldHidden(targetField, fieldsMap)).toBe(false);
  });
});

describe('updateFieldsHidden + getVisibleFields: runtime form visibility synchronization', () => {
  it('recalculates kickoff and fieldset fields visibility without removing fieldset structure', () => {
    const categoryField = makeExtraField({ apiName: 'category', value: 'VIP' });
    const nameField = makeExtraField({ apiName: 'user-name', value: 'John', isHidden: false });

    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({ field: 'category', operator: EFieldRuleOperator.Equal, value: 'VIP' }),
          ],
        }),
      ],
    });

    const vipExtraField = makeExtraField({
      apiName: 'vip-pass',
      isHidden: true,
      rulesets: [showRuleset],
    });

    const fieldset = makeFieldsetRuntime({
      fields: [vipExtraField],
    });

    const updated1 = updateFieldsHidden([categoryField, nameField], [fieldset]);
    const visible1 = getVisibleFields(updated1.fields, updated1.fieldsets);
    expect(visible1.visibleFields).toHaveLength(2);
    expect(visible1.visibleFieldsets[0].fields).toHaveLength(1);
    expect(visible1.visibleFieldsets[0].fields[0].apiName).toBe('vip-pass');

    categoryField.value = 'Standard';
    const updated2 = updateFieldsHidden([categoryField, nameField], [fieldset]);
    const visible2 = getVisibleFields(updated2.fields, updated2.fieldsets);
    expect(visible2.visibleFields).toHaveLength(2);
    expect(visible2.visibleFieldsets).toHaveLength(1);
    expect(visible2.visibleFieldsets[0].fields).toHaveLength(0);
  });
});

describe('getVisibleFieldsByShowRules: wrapper for updateFieldsHidden + getVisibleFields', () => {
  it('returns only visible fields after applying show rulesets in a single call', () => {
    const triggerField = makeExtraField({ apiName: 'trigger', value: 'show' });
    const alwaysVisibleField = makeExtraField({ apiName: 'always-visible', isHidden: false });

    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({ field: 'trigger', operator: EFieldRuleOperator.Equal, value: 'show' }),
          ],
        }),
      ],
    });

    const conditionalField = makeExtraField({
      apiName: 'conditional',
      isHidden: true,
      rulesets: [showRuleset],
    });

    const fieldset = makeFieldsetRuntime({ fields: [conditionalField] });

    const result1 = getVisibleFieldsByShowRules([triggerField, alwaysVisibleField], [fieldset]);
    expect(result1.visibleFields).toHaveLength(2);
    expect(result1.visibleFieldsets[0].fields).toHaveLength(1);

    triggerField.value = 'hide';
    const result2 = getVisibleFieldsByShowRules([triggerField, alwaysVisibleField], [fieldset]);
    expect(result2.visibleFields).toHaveLength(2);
    expect(result2.visibleFieldsets[0].fields).toHaveLength(0);
  });
});

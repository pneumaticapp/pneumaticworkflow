import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { EExtraFieldType } from '../../../../types/template';
import { EFieldRuleType } from '../../../../types/fieldset';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldRuleSet } from '../../../../__stubs__/fieldsets.factory';
import { useFieldRuleModal } from '../useFieldRuleModal';

type HookResult = ReturnType<typeof useFieldRuleModal>;
let hookResult: HookResult;

const fieldA = makeExtraField({ apiName: 'field-a', name: 'Field A', type: EExtraFieldType.String });
const fieldB = makeExtraField({ apiName: 'field-b', name: 'Field B', type: EExtraFieldType.Number });

function HookHarness({ fields, onFieldsChange }: { fields: typeof fieldA[]; onFieldsChange: jest.Mock }) {
  hookResult = useFieldRuleModal(fields, onFieldsChange);

  return (
    <div>
      <button data-testid="open" onClick={() => hookResult.openFieldRule('field-a')} />
      <button data-testid="open-edit" onClick={() => hookResult.openFieldRule('field-a', makeFieldRuleSet())} />
      <button data-testid="save" onClick={() => hookResult.fieldRuleModalProps.onSave(makeFieldRuleSet({ apiName: 'new-rule' }))} />
      <button data-testid="close" onClick={() => hookResult.fieldRuleModalProps.onClose()} />
      <button data-testid="delete" onClick={() => hookResult.handleDeleteFieldRuleset('field-a', 'rule-1')} />
      <span data-testid="is-open">{String(hookResult.fieldRuleModalProps.isOpen)}</span>
    </div>
  );
}

describe('useFieldRuleModal', () => {
  const setup = (fields = [fieldA, fieldB]) => {
    const onFieldsChange = jest.fn();
    const renderResult = render(<HookHarness fields={fields} onFieldsChange={onFieldsChange} />);
    return { onFieldsChange, ...renderResult };
  };

  it('starts with modal closed', () => {
    setup();
    expect(hookResult.fieldRuleModalProps.isOpen).toBe(false);
    expect(hookResult.fieldRuleModalProps.fieldType).toBeUndefined();
  });

  it('opens modal with correct field data on openFieldRule', () => {
    setup();
    userEvent.click(screen.getByTestId('open'));

    expect(hookResult.fieldRuleModalProps.isOpen).toBe(true);
    expect(hookResult.fieldRuleModalProps.fieldType).toBe(EExtraFieldType.String);
    expect(hookResult.fieldRuleModalProps.ruleset).toBeNull();
  });

  it('opens modal with existing ruleset for editing', () => {
    setup();
    userEvent.click(screen.getByTestId('open-edit'));

    expect(hookResult.fieldRuleModalProps.isOpen).toBe(true);
    expect(hookResult.fieldRuleModalProps.ruleset).toEqual(expect.objectContaining({ type: EFieldRuleType.Validator }));
  });

  it('closes modal on handleFieldRuleClose', () => {
    setup();
    userEvent.click(screen.getByTestId('open'));
    expect(hookResult.fieldRuleModalProps.isOpen).toBe(true);

    userEvent.click(screen.getByTestId('close'));
    expect(hookResult.fieldRuleModalProps.isOpen).toBe(false);
  });

  it('calls onFieldsChange with updated fields on save', () => {
    const { onFieldsChange } = setup();
    userEvent.click(screen.getByTestId('open'));
    userEvent.click(screen.getByTestId('save'));

    expect(onFieldsChange).toHaveBeenCalledTimes(1);
    const updatedFields = onFieldsChange.mock.calls[0][0];
    const savedField = updatedFields.find((field: { apiName: string }) => field.apiName === 'field-a');
    expect(savedField.rulesets).toEqual(expect.arrayContaining([
      expect.objectContaining({ apiName: 'new-rule' }),
    ]));
  });

  it('closes modal after save', () => {
    setup();
    userEvent.click(screen.getByTestId('open'));
    userEvent.click(screen.getByTestId('save'));

    expect(hookResult.fieldRuleModalProps.isOpen).toBe(false);
  });

  it('excludes active field from fieldRuleShowFieldOptions', () => {
    setup();
    userEvent.click(screen.getByTestId('open'));

    const options = hookResult.fieldRuleModalProps.fieldRuleShowFieldOptions;
    expect(options).toHaveLength(1);
    expect(options[0].apiName).toBe('field-b');
  });

  it('calls onFieldsChange on deleteFieldRuleset', () => {
    const rulesetToDelete = makeFieldRuleSet({ apiName: 'rule-1' });
    const fieldWithRuleset = makeExtraField({
      apiName: 'field-a',
      rulesets: [rulesetToDelete],
    });
    const { onFieldsChange } = setup([fieldWithRuleset, fieldB]);

    userEvent.click(screen.getByTestId('delete'));

    expect(onFieldsChange).toHaveBeenCalledTimes(1);
    const updatedFields = onFieldsChange.mock.calls[0][0];
    const deletedField = updatedFields.find((field: { apiName: string }) => field.apiName === 'field-a');
    expect(deletedField.rulesets).toHaveLength(0);
  });
});

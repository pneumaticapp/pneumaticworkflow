import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient, makeFieldsetField } from '../../../../__stubs__/fieldsets.factory';
import { IExtraField } from '../../../../types/template';
import { intlMock } from '../../../../__stubs__/intlMock';
import { MergedOutputRows, IMergedOutputRowsProps } from '../MergedOutputRows';
import { TMergedTaskOutputRow } from '../mergeTaskOutputFlow';
import { IFieldRuleSet } from '../../../../types/fieldset';
import { makeFieldRuleSet } from '../../../../__stubs__/fieldsets.factory';

type TExtraFieldIntlMockProps = {
  field: IExtraField;
  moveFieldUp?: () => void;
  moveFieldDown?: () => void;
  fieldRulesets?: IFieldRuleSet[];
  onOpenFieldRules?: (ruleset?: IFieldRuleSet) => void;
  onDeleteFieldRuleset?: (rulesetApiName: string) => void;
};

type TFieldsetFlowRowDropdownMockProps = {
  onMoveUp: () => void;
  onMoveDown: () => void;
  onRemove: () => void;
};

jest.mock('../../ExtraFields', () => ({
  ExtraFieldIntl: ({ field, moveFieldUp, moveFieldDown, onOpenFieldRules, fieldRulesets, onDeleteFieldRuleset }: TExtraFieldIntlMockProps) =>
    React.createElement(
      'div',
      { 'data-testid': 'extra-field-intl' },
      field.name,
      moveFieldUp
        && React.createElement(
          'button',
          { 'data-testid': `field-up-${field.apiName}`, onClick: moveFieldUp },
          'FieldUp',
        ),
      moveFieldDown
        && React.createElement(
          'button',
          { 'data-testid': `field-down-${field.apiName}`, onClick: moveFieldDown },
          'FieldDown',
        ),
      onOpenFieldRules
        && React.createElement(
          'button',
          { 'data-testid': `open-rules-${field.apiName}`, onClick: () => onOpenFieldRules() },
          'OpenRules',
        ),
      fieldRulesets
        && React.createElement(
          'span',
          { 'data-testid': `rulesets-count-${field.apiName}` },
          String(fieldRulesets.length),
        ),
      onDeleteFieldRuleset
        && React.createElement(
          'button',
          { 'data-testid': `delete-rule-${field.apiName}`, onClick: () => onDeleteFieldRuleset('rule-1') },
          'DeleteRule',
        ),
    ),
}));

jest.mock('../../ExtraFields/utils/ExtraFieldsLabels', () => ({
  ExtraFieldsLabels: () =>
    React.createElement('div', { 'data-testid': 'extra-fields-labels' }),
}));

jest.mock('../FieldsetFlowRowDropdown', () => ({
  FieldsetFlowRowDropdown: ({
    onMoveUp,
    onMoveDown,
    onRemove,
  }: TFieldsetFlowRowDropdownMockProps) =>
    React.createElement(
      'div',
      null,
      React.createElement('button', { onClick: onMoveUp }, 'Up'),
      React.createElement('button', { onClick: onMoveDown }, 'Down'),
      React.createElement('button', { onClick: onRemove }, 'Remove'),
    ),
}));

jest.mock('../FieldsetEditorTitle', () => ({
  FieldsetEditorTitle: ({ title }: { title: string }) =>
    React.createElement('div', { 'data-testid': 'fieldset-editor-title' }, title),
}));

const makeField = (apiName: string) => makeExtraField({
  apiName,
  name: `Field ${apiName}`,
});

const fieldRow = (apiName: string): TMergedTaskOutputRow => ({
  kind: 'field',
  field: makeField(apiName),
});

const fieldsetRow = (apiNameBinding: string, name = 'Test Fieldset', fieldsCount = 0, title?: string): TMergedTaskOutputRow => ({
  ...makeFieldsetBindingClient({
    apiNameBinding,
    name,
    title: title ?? `Title of ${name}`,
    fields: Array.from({ length: fieldsCount }, (_, index) =>
      makeFieldsetField({ apiName: `${apiNameBinding}-field-${index}` }),
    ),
  }),
  kind: 'fieldset',
});

describe('MergedOutputRows', () => {
  const makeProps = (overrides: Partial<IMergedOutputRowsProps> = {}): IMergedOutputRowsProps => ({
    mergedRows: [],
    onDeleteField: jest.fn(),
    onMoveRow: jest.fn(),
    onEditField: jest.fn(() => jest.fn()),
    onRemoveFieldset: jest.fn(),
    onEditFieldsetTitle: jest.fn(),
    datasetOptions: [],
    accountId: 1,
    formatMessage: intlMock.formatMessage,
    ...overrides,
  });

  it('field row renders ExtraFieldIntl with the field name', () => {
    render(
      React.createElement(MergedOutputRows, makeProps({ mergedRows: [fieldRow('f-1')] })),
    );
    expect(screen.getByText('Field f-1')).toBeInTheDocument();
  });

  it('fieldset row → renders header with catalog name inline and FieldsetEditorTitle with title', () => {
    const HEADER_LABEL = intlMock.formatMessage({ id: 'fieldsets.header-label' });

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({
          mergedRows: [
            fieldsetRow('fs-1', 'Fieldset Alpha', 0, 'Custom Title Alpha'),
          ],
        }),
      ),
    );

    expect(screen.getByText(`${HEADER_LABEL}: Fieldset Alpha`)).toBeInTheDocument();
    expect(screen.getByTestId('fieldset-editor-title')).toHaveTextContent('Custom Title Alpha');
  });

  it('renders ExtraFieldsLabels when fieldset has fields', () => {
    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1', 'Fieldset A', 2)] }),
      ),
    );

    expect(screen.getByTestId('extra-fields-labels')).toBeInTheDocument();
  });

  it('does NOT render ExtraFieldsLabels when fieldset has no fields', () => {
    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1', 'Fieldset A', 0)] }),
      ),
    );

    expect(screen.queryByTestId('extra-fields-labels')).not.toBeInTheDocument();
  });

  it('renders FieldsetFlowRowDropdown for kind=fieldset rows', () => {
    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')] }),
      ),
    );

    expect(screen.getByRole('button', { name: 'Remove' })).toBeInTheDocument();
  });

  it('click Remove → onRemoveFieldset(apiNameBinding) called once', () => {
    const onRemoveFieldset = jest.fn();

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], onRemoveFieldset }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(onRemoveFieldset).toHaveBeenCalledTimes(1);
    expect(onRemoveFieldset).toHaveBeenCalledWith('fs-1');
  });

  it('click Up → onMoveRow(0, "up") called once, "down" not called', () => {
    const onMoveRow = jest.fn();

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], onMoveRow }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: 'Up' }));

    expect(onMoveRow).toHaveBeenCalledTimes(1);
    expect(onMoveRow).toHaveBeenCalledWith(0, 'up');
    expect(onMoveRow).not.toHaveBeenCalledWith(expect.anything(), 'down');
  });

  it('click Down → onMoveRow(0, "down") called once, "up" not called', () => {
    const onMoveRow = jest.fn();

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], onMoveRow }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: 'Down' }));

    expect(onMoveRow).toHaveBeenCalledTimes(1);
    expect(onMoveRow).toHaveBeenCalledWith(0, 'down');
    expect(onMoveRow).not.toHaveBeenCalledWith(expect.anything(), 'up');
  });

  it('field rows: first has only Down, middle has both, last has only Up', () => {
    const rows: TMergedTaskOutputRow[] = [
      fieldRow('f-0'),
      fieldRow('f-1'),
      fieldRow('f-2'),
    ];

    render(
      React.createElement(MergedOutputRows, makeProps({ mergedRows: rows })),
    );

    expect(screen.queryByTestId('field-up-f-0')).not.toBeInTheDocument();
    expect(screen.getByTestId('field-down-f-0')).toBeInTheDocument();

    expect(screen.getByTestId('field-up-f-1')).toBeInTheDocument();
    expect(screen.getByTestId('field-down-f-1')).toBeInTheDocument();

    expect(screen.getByTestId('field-up-f-2')).toBeInTheDocument();
    expect(screen.queryByTestId('field-down-f-2')).not.toBeInTheDocument();
  });

  describe('field rule props passthrough', () => {
    it('passes fieldRulesets and onOpenFieldRules to ExtraFieldIntl when provided', () => {
      const ruleset = makeFieldRuleSet({ apiName: 'rule-1' });
      const fieldWithRulesets = makeExtraField({
        apiName: 'f-rules',
        name: 'Field With Rules',
        rulesets: [ruleset],
      });
      const fieldRowWithRules: TMergedTaskOutputRow = { kind: 'field', field: fieldWithRulesets };
      const onOpenFieldRules = jest.fn();
      const onDeleteFieldRuleset = jest.fn();

      render(
        React.createElement(
          MergedOutputRows,
          makeProps({
            mergedRows: [fieldRowWithRules],
            onOpenFieldRules,
            onDeleteFieldRuleset,
          }),
        ),
      );

      expect(screen.getByTestId('rulesets-count-f-rules')).toHaveTextContent('1');
      expect(screen.getByTestId('open-rules-f-rules')).toBeInTheDocument();
      expect(screen.getByTestId('delete-rule-f-rules')).toBeInTheDocument();
    });

    it('does not pass field rule props when onOpenFieldRules is not provided', () => {
      render(
        React.createElement(
          MergedOutputRows,
          makeProps({ mergedRows: [fieldRow('f-1')] }),
        ),
      );

      expect(screen.queryByTestId('open-rules-f-1')).not.toBeInTheDocument();
      expect(screen.queryByTestId('rulesets-count-f-1')).not.toBeInTheDocument();
    });

    it('click OpenRules calls onOpenFieldRules with fieldApiName', () => {
      const onOpenFieldRules = jest.fn();

      render(
        React.createElement(
          MergedOutputRows,
          makeProps({
            mergedRows: [fieldRow('f-1')],
            onOpenFieldRules,
          }),
        ),
      );

      userEvent.click(screen.getByTestId('open-rules-f-1'));

      expect(onOpenFieldRules).toHaveBeenCalledTimes(1);
      expect(onOpenFieldRules).toHaveBeenCalledWith('f-1', undefined);
    });

    it('click DeleteRule calls onDeleteFieldRuleset with fieldApiName and rulesetApiName', () => {
      const onDeleteFieldRuleset = jest.fn();

      render(
        React.createElement(
          MergedOutputRows,
          makeProps({
            mergedRows: [fieldRow('f-1')],
            onOpenFieldRules: jest.fn(),
            onDeleteFieldRuleset,
          }),
        ),
      );

      userEvent.click(screen.getByTestId('delete-rule-f-1'));

      expect(onDeleteFieldRuleset).toHaveBeenCalledTimes(1);
      expect(onDeleteFieldRuleset).toHaveBeenCalledWith('f-1', 'rule-1');
    });
  });
});

import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient, makeFieldsetField } from '../../../../__stubs__/fieldsets.factory';
import { IExtraField } from '../../../../types/template';
import { intlMock } from '../../../../__stubs__/intlMock';
import { MergedOutputRows, IMergedOutputRowsProps } from '../MergedOutputRows';
import { TMergedTaskOutputRow } from '../mergeTaskOutputFlow';

type TExtraFieldIntlMockProps = {
  field: IExtraField;
  moveFieldUp?: () => void;
  moveFieldDown?: () => void;
};

type TFieldsetFlowRowDropdownMockProps = {
  onMoveUp: () => void;
  onMoveDown: () => void;
  onRemove: () => void;
};

jest.mock('../../ExtraFields', () => ({
  ExtraFieldIntl: ({ field, moveFieldUp, moveFieldDown }: TExtraFieldIntlMockProps) =>
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

const makeField = (apiName: string) => makeExtraField({
  apiName,
  name: `Field ${apiName}`,
});

const fieldRow = (apiName: string): TMergedTaskOutputRow => ({
  kind: 'field',
  field: makeField(apiName),
});

const fieldsetRow = (apiNameBinding: string, name = 'Test Fieldset', fieldsCount = 0): TMergedTaskOutputRow => ({
  ...makeFieldsetBindingClient({
    apiNameBinding,
    name,
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

  it('fieldset with name → renders "<prefix>: <name>" with exact text', () => {
    const prefix = intlMock.formatMessage({ id: 'fieldsets.title' });

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1', 'Fieldset Alpha')] }),
      ),
    );

    expect(screen.getByText(`${prefix}: Fieldset Alpha`)).toBeInTheDocument();
  });

  it('fieldset with empty name → renders "<prefix>: <fallback>" with exact text', () => {
    const prefix = intlMock.formatMessage({ id: 'fieldsets.title' });
    const fallback = intlMock.formatMessage({ id: 'tasks.task-fieldsets' });

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-empty', '')] }),
      ),
    );

    expect(screen.getByText(`${prefix}: ${fallback}`)).toBeInTheDocument();
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

  it('click Remove → onRemoveFieldset(sharedFieldsetId) called once', () => {
    const onRemoveFieldset = jest.fn();

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], onRemoveFieldset }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(onRemoveFieldset).toHaveBeenCalledTimes(1);
    expect(onRemoveFieldset).toHaveBeenCalledWith(1);
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
});

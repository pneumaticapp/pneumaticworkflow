import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
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

const makeField = (apiName: string): IExtraField => ({
  apiName,
  name: `Field ${apiName}`,
  type: EExtraFieldType.String,
  order: 0,
  isRequired: false,
  isHidden: false,
  userId: null,
  groupId: null,
  description: '',
  selections: [],
});

const makeFieldsetData = (apiName: string, fieldsCount: number): IFieldsetData => ({
  id: 1,
  apiName,
  name: `Fieldset ${apiName}`,
  description: '',
  order: 0,
  labelPosition: EFieldLabelPosition.Top,
  fields: Array.from({ length: fieldsCount }, (_, i) => makeField(`${apiName}-field-${i}`)),
  rulesCount: 0,
} as IFieldsetData);

const fieldRow = (apiName: string): TMergedTaskOutputRow => ({
  kind: 'field',
  field: makeField(apiName),
});

const fieldsetRow = (apiName: string): TMergedTaskOutputRow => ({
  kind: 'fieldset',
  apiName,
  order: 0,
});

describe('MergedOutputRows', () => {
  const makeProps = (overrides: Partial<IMergedOutputRowsProps> = {}): IMergedOutputRowsProps => ({
    mergedRows: [],
    fieldsetsByApiName: new Map(),
    onDeleteField: jest.fn(),
    onMoveRow: jest.fn(),
    onEditField: jest.fn(() => jest.fn()),
    onRemoveFieldset: jest.fn(),
    datasetOptions: [],
    accountId: 1,
    formatMessage: intlMock.formatMessage,
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('field row renders ExtraFieldIntl with the field name', () => {
    render(
      React.createElement(MergedOutputRows, makeProps({ mergedRows: [fieldRow('f-1')] })),
    );
    expect(screen.getByText('Field f-1')).toBeInTheDocument();
  });

  it('fieldset found in fieldsetsByApiName → renders "<prefix>: <name>" with exact text', () => {
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);
    const prefix = intlMock.formatMessage({ id: 'fieldsets.title' });

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map }),
      ),
    );

    expect(screen.getByText(`${prefix}: Fieldset fs-1`)).toBeInTheDocument();
  });

  it('fieldset not found in map → renders "<prefix>: <fallback>" with exact text', () => {
    const prefix = intlMock.formatMessage({ id: 'fieldsets.title' });
    const fallback = intlMock.formatMessage({ id: 'tasks.task-fieldsets' });

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-missing')], fieldsetsByApiName: new Map() }),
      ),
    );

    expect(screen.getByText(`${prefix}: ${fallback}`)).toBeInTheDocument();
  });

  it('renders ExtraFieldsLabels when fieldset has fields', () => {
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 2)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map }),
      ),
    );

    expect(screen.getByTestId('extra-fields-labels')).toBeInTheDocument();
  });

  it('does NOT render ExtraFieldsLabels when fieldset has no fields', () => {
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map }),
      ),
    );

    expect(screen.queryByTestId('extra-fields-labels')).not.toBeInTheDocument();
  });

  it('renders FieldsetFlowRowDropdown for kind=fieldset rows', () => {
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map }),
      ),
    );

    expect(screen.getByRole('button', { name: 'Remove' })).toBeInTheDocument();
  });

  it('click Remove → onRemoveFieldset("fs-1") called once', () => {
    const onRemoveFieldset = jest.fn();
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map, onRemoveFieldset }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(onRemoveFieldset).toHaveBeenCalledTimes(1);
    expect(onRemoveFieldset).toHaveBeenCalledWith('fs-1');
  });

  it('click Up → onMoveRow(0, "up") called once, "down" not called', () => {
    const onMoveRow = jest.fn();
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map, onMoveRow }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: 'Up' }));

    expect(onMoveRow).toHaveBeenCalledTimes(1);
    expect(onMoveRow).toHaveBeenCalledWith(0, 'up');
    expect(onMoveRow).not.toHaveBeenCalledWith(expect.anything(), 'down');
  });

  it('click Down → onMoveRow(0, "down") called once, "up" not called', () => {
    const onMoveRow = jest.fn();
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map, onMoveRow }),
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

// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../../types/template';
import { intlMock } from '../../../../__stubs__/intlMock';
import { MergedOutputRows, IMergedOutputRowsProps } from '../MergedOutputRows';
import { TMergedTaskOutputRow } from '../mergeTaskOutputFlow';

jest.mock('../../ExtraFields', () => ({
  ExtraFieldIntl: ({ field }: any) => {
    const R = require('react');
    return R.createElement('div', { 'data-testid': 'extra-field-intl' }, field.name);
  },
}));

jest.mock('../../ExtraFields/utils/ExtraFieldsLabels', () => ({
  ExtraFieldsLabels: () => {
    const R = require('react');
    return R.createElement('div', { 'data-testid': 'extra-fields-labels' });
  },
}));

jest.mock('../FieldsetFlowRowDropdown', () => ({
  FieldsetFlowRowDropdown: ({ onMoveUp, onMoveDown, onRemove }: any) => {
    const R = require('react');
    return R.createElement(
      'div',
      null,
      R.createElement('button', { onClick: onMoveUp }, 'Up'),
      R.createElement('button', { onClick: onMoveDown }, 'Down'),
      R.createElement('button', { onClick: onRemove }, 'Remove'),
    );
  },
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

  it('fieldset found in fieldsetsByApiName → renders its name', () => {
    const map = new Map<string, IFieldsetData>([['fs-1', makeFieldsetData('fs-1', 0)]]);

    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-1')], fieldsetsByApiName: map }),
      ),
    );

    expect(screen.getByText(/Fieldset fs-1/)).toBeInTheDocument();
  });

  it('fieldset not found in map → renders fallback text', () => {
    render(
      React.createElement(
        MergedOutputRows,
        makeProps({ mergedRows: [fieldsetRow('fs-missing')], fieldsetsByApiName: new Map() }),
      ),
    );

    const fallback = intlMock.formatMessage({ id: 'tasks.task-fieldsets' });
    expect(screen.getByText(new RegExp(fallback))).toBeInTheDocument();
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
});

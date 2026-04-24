// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldCreatable } from '../ExtraFieldCreatable';
import { DatasetSourceToggle } from '../../utils/DatasetSourceToggle';
import { DropdownList } from '../../../../UI/DropdownList';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EExtraFieldMode } from '../../../../../types/template';

jest.mock('../../utils/DatasetSourceToggle', () => ({
  DatasetSourceToggle: jest.fn(({ children }: any) =>
    React.createElement('div', { 'data-testid': 'dataset-source-toggle' }, children),
  ),
}));

jest.mock('../../../../UI/DropdownList', () => ({
  DropdownList: jest.fn(() => React.createElement('div', { 'data-testid': 'dropdown-list' })),
}));

jest.mock('../../../../icons', () => ({
  RemoveIcon: () => null,
  ArrowDropdownIcon: () => null,
}));

jest.mock('../../../../../utils/validators', () => ({
  validateCheckboxAndRadioField: jest.fn(() => ''),
}));

jest.mock('../../utils/handleSelectionBlur', () => ({
  handleSelectionBlur: jest.fn(() => jest.fn(() => jest.fn())),
  recalculateDuplicateErrors: jest.fn(() => ({})),
}));

jest.mock('../../utils/fitInputWidth', () => ({
  fitInputWidth: jest.fn(),
}));

jest.mock('../../utils/getInputNameBackground', () => ({
  getInputNameBackground: jest.fn(() => ''),
}));

jest.mock('../../utils/getFieldValidator', () => ({
  getFieldValidator: jest.fn(() => jest.fn(() => '')),
}));

jest.mock('../../../../IntlMessages', () => ({
  IntlMessages: jest.fn(() => null),
}));

jest.mock('../../utils/FieldWithName', () => ({
  FieldWithName: jest.fn(() => React.createElement('div', { 'data-testid': 'field-with-name' })),
}));

jest.mock('../../../KickoffRedux/utils/getEmptySelection', () => ({
  getEmptySelection: jest.fn(() => ({ id: 'empty', value: '', isSelected: false, apiName: 'empty' })),
}));

describe('ExtraFieldCreatable', () => {
  const mockEditField = jest.fn();

  const kickoffField = {
    name: 'Priority',
    value: '',
    type: 'creatable' as any,
    apiName: 'priority',
    order: 0,
    isRequired: false,
    userId: 1,
    groupId: 1,
    dataset: null,
    description: 'Select priority',
    selections: [
      { id: 1, value: 'High', isSelected: false, apiName: 'opt-1' },
      { id: 2, value: 'Low', isSelected: false, apiName: 'opt-2' },
    ],
  };

  const processRunField = {
    ...kickoffField,
    selections: ['High', 'Medium', 'Low'],
    value: 'High',
  };

  const baseKickoffProps = {
    field: kickoffField as any,
    intl: intlMock as any,
    editField: mockEditField,
    mode: EExtraFieldMode.Kickoff,
    isDisabled: false,
    accountId: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('Kickoff: renders DatasetSourceToggle as wrapper for options', () => {
    render(React.createElement(ExtraFieldCreatable as any, baseKickoffProps));

    expect(screen.getByTestId('dataset-source-toggle')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to DatasetSourceToggle', () => {
    render(React.createElement(ExtraFieldCreatable as any, baseKickoffProps));

    const mock = DatasetSourceToggle as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(1);
    expect(mock).toHaveBeenCalledWith(
      expect.objectContaining({
        field: kickoffField,
        editField: mockEditField,
        isDisabled: false,
      }),
      {},
    );
  });

  it('ProcessRun: renders DropdownList with string selections as options', () => {
    render(React.createElement(ExtraFieldCreatable as any, {
      ...baseKickoffProps,
      field: processRunField as any,
      mode: EExtraFieldMode.ProcessRun,
    }));

    const mock = DropdownList as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(1);
    expect(mock).toHaveBeenCalledWith(
      expect.objectContaining({
        options: [
          { value: 'High', label: 'High' },
          { value: 'Medium', label: 'Medium' },
          { value: 'Low', label: 'Low' },
        ],
      }),
      {},
    );
  });
});

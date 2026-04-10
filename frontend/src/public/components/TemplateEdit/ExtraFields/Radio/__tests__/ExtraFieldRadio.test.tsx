// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldRadio } from '../ExtraFieldRadio';
import { DatasetSourceToggle } from '../../utils/DatasetSourceToggle';
import { RadioButton } from '../../../../UI/Fields/RadioButton';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EExtraFieldMode } from '../../../../../types/template';

jest.mock('../../utils/DatasetSourceToggle', () => ({
  DatasetSourceToggle: jest.fn(({ children }: any) =>
    React.createElement('div', { 'data-testid': 'dataset-source-toggle' }, children),
  ),
}));

jest.mock('../../../../UI/Fields/RadioButton', () => ({
  RadioButton: jest.fn(({ title }: any) =>
    React.createElement('span', { 'data-testid': `radio-${title}` }, title),
  ),
}));

jest.mock('react-input-autosize', () => ({
  __esModule: true,
  default: jest.fn(({ value, onChange, placeholder }: any) =>
    React.createElement('input', { value: value || '', onChange, placeholder }),
  ),
}));

jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
  RemoveIcon: () => null,
}));

jest.mock('../../../../../utils/validators', () => ({
  validateCheckboxAndRadioField: jest.fn(() => ''),
  validateKickoffFieldName: jest.fn(() => ''),
}));

jest.mock('../../utils/handleSelectionBlur', () => ({
  handleSelectionBlur: jest.fn(() => jest.fn(() => jest.fn())),
  recalculateDuplicateErrors: jest.fn(() => ({})),
}));

jest.mock('../../utils/fitInputWidth', () => ({
  fitInputWidth: jest.fn(),
}));

jest.mock('../../../../IntlMessages', () => ({
  IntlMessages: jest.fn(() => null),
}));

jest.mock('../../../KickoffRedux/utils/getEmptySelection', () => ({
  getEmptySelection: jest.fn(() => ({ id: 'empty', value: '', isSelected: false, apiName: 'empty' })),
}));

describe('ExtraFieldRadio', () => {
  const mockEditField = jest.fn();

  const kickoffField = {
    name: 'Color',
    value: '',
    type: 'radio' as any,
    apiName: 'color',
    order: 0,
    isRequired: false,
    userId: 1,
    groupId: 1,
    dataset: null,
    selections: [
      { id: 1, value: 'Red', isSelected: false, apiName: 'opt-1' },
      { id: 2, value: 'Blue', isSelected: false, apiName: 'opt-2' },
    ],
  };

  const processRunField = {
    ...kickoffField,
    selections: ['Red', 'Blue', 'Green'],
    value: 'Red',
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
    render(React.createElement(ExtraFieldRadio as any, baseKickoffProps));

    expect(screen.getByTestId('dataset-source-toggle')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to DatasetSourceToggle', () => {
    render(React.createElement(ExtraFieldRadio as any, baseKickoffProps));

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

  it('ProcessRun: renders RadioButton for each string selection', () => {
    render(React.createElement(ExtraFieldRadio as any, {
      ...baseKickoffProps,
      field: processRunField as any,
      mode: EExtraFieldMode.ProcessRun,
    }));

    const mock = RadioButton as unknown as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(3);
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Red' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Blue' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Green' }), {});
  });
});

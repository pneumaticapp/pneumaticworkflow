// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldCheckbox } from '../ExtraFieldCheckbox';
import { OutputFieldContent } from '../../utils/OutputFieldContent';
import { Checkbox } from '../../../../UI/Fields/Checkbox';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EExtraFieldMode } from '../../../../../types/template';

jest.mock('../../utils/OutputFieldContent', () => ({
  OutputFieldContent: jest.fn(({ children }: any) =>
    React.createElement('div', { 'data-testid': 'output-field-content' }, children),
  ),
}));

jest.mock('../../../../UI/Fields/Checkbox', () => ({
  Checkbox: jest.fn(({ title }: any) =>
    React.createElement('span', { 'data-testid': `checkbox-${title}` }, title),
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

describe('ExtraFieldCheckbox', () => {
  const mockEditField = jest.fn();

  const kickoffField = {
    name: 'Colors',
    value: '',
    type: 'checkbox' as any,
    apiName: 'colors',
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

  it('Kickoff: renders OutputFieldContent as wrapper for options', () => {
    render(React.createElement(ExtraFieldCheckbox as any, baseKickoffProps));

    expect(screen.getByTestId('output-field-content')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to OutputFieldContent', () => {
    render(React.createElement(ExtraFieldCheckbox as any, baseKickoffProps));

    const mock = OutputFieldContent as jest.Mock;
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

  it('ProcessRun: renders Checkbox for each string selection', () => {
    render(React.createElement(ExtraFieldCheckbox as any, {
      ...baseKickoffProps,
      field: processRunField as any,
      mode: EExtraFieldMode.ProcessRun,
    }));

    const mock = Checkbox as unknown as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(3);
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Red' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Blue' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Green' }), {});
  });
});

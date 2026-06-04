// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldRadio } from '../ExtraFieldRadio';
import { OutputFieldContent } from '../../utils/OutputFieldContent';
import { RadioButton } from '../../../../UI/Fields/RadioButton';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EExtraFieldMode, EExtraFieldType } from '../../../../../types/template';
import { IWorkflowExtraFieldProps } from '../../types';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';

jest.mock('../../utils/OutputFieldContent', () => ({
  OutputFieldContent: jest.fn(({ children }: any) =>
    React.createElement('div', { 'data-testid': 'output-field-content' }, children),
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

  it('Kickoff: renders OutputFieldContent as wrapper for options', () => {
    render(React.createElement(ExtraFieldRadio as any, baseKickoffProps));

    expect(screen.getByTestId('output-field-content')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to OutputFieldContent', () => {
    render(React.createElement(ExtraFieldRadio as any, baseKickoffProps));

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

  describe('unique radio grouping across multiple fields', () => {
    it('ProcessRun: two fields with identical selections receive unique RadioButton ids', () => {
      const sharedSelections = ['Red', 'Blue'];

      const field1 = makeExtraField({
        apiName: 'radio-1',
        name: 'Color',
        type: EExtraFieldType.Radio,
        selections: sharedSelections,
        value: 'Red',
      });

      const field2 = makeExtraField({
        apiName: 'radio-2',
        name: 'Color',
        type: EExtraFieldType.Radio,
        selections: sharedSelections,
        value: null,
      });

      const commonProps: Omit<IWorkflowExtraFieldProps, 'field'> = {
        intl: intlMock,
        editField: mockEditField,
        mode: EExtraFieldMode.ProcessRun,
        isDisabled: false,
        accountId: 1,
      };

      // @ts-expect-error master version returns ReactNode; after fieldsets merge this becomes JSX.Element and labelPosition must be added
      render(<ExtraFieldRadio {...commonProps} field={field1} />);
      // @ts-expect-error master version returns ReactNode; after fieldsets merge this becomes JSX.Element and labelPosition must be added
      render(<ExtraFieldRadio {...commonProps} field={field2} />);

      const mock = RadioButton as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(4);
      const allIds = mock.mock.calls.map((call: [Record<string, unknown>]) => call[0].id as string);

      const uniqueIds = new Set(allIds);
      expect(uniqueIds.size).toBe(allIds.length);

      const field1Ids = allIds.filter((id: string) => id.includes('radio-1'));
      expect(field1Ids).toHaveLength(sharedSelections.length);

      const field2Ids = allIds.filter((id: string) => id.includes('radio-2'));
      expect(field2Ids).toHaveLength(sharedSelections.length);
    });
  });
});

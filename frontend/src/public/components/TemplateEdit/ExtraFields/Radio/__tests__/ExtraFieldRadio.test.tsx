import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldRadio } from '../ExtraFieldRadio';
import { OutputFieldContent } from '../../utils/OutputFieldContent';
import { FieldLabel } from '../../utils/FieldLabel';
import { RadioButton } from '../../../../UI/Fields/RadioButton';
import { IWorkflowExtraFieldProps } from '../../types';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldMode, EExtraFieldType, IExtraFieldSelection } from '../../../../../types/template';
import { EFieldLabelPosition } from '../../../../../types/fieldset';

jest.mock('../../utils/OutputFieldContent', () => ({
  OutputFieldContent: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'output-field-content' }, children),
  ),
}));

jest.mock('../../../../UI/Fields/RadioButton', () => ({
  RadioButton: jest.fn(({ title }: { title: string }) =>
    React.createElement('span', { 'data-testid': `radio-${title}` }, title),
  ),
}));

jest.mock('react-input-autosize', () => ({
  __esModule: true,
  default: jest.fn(({ value, onChange, placeholder }: { value: string; onChange: () => void; placeholder: string }) =>
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

jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

describe('ExtraFieldRadio', () => {
  const mockEditField = jest.fn();

  const kickoffSelections: IExtraFieldSelection[] = [
    { key: 1, value: 'Red', isSelected: false, apiName: 'opt-1' },
    { key: 2, value: 'Blue', isSelected: false, apiName: 'opt-2' },
  ];

  const processRunSelections = ['Red', 'Blue', 'Green'];

  const kickoffField = makeExtraField({
    name: 'Color',
    type: EExtraFieldType.Radio,
    selections: kickoffSelections,
  });

  const processRunField = makeExtraField({
    name: 'Color',
    type: EExtraFieldType.Radio,
    selections: processRunSelections,
    value: 'Red',
  });

  const baseKickoffProps: IWorkflowExtraFieldProps = {
    field: kickoffField,
    intl: intlMock,
    editField: mockEditField,
    mode: EExtraFieldMode.Kickoff,
    isDisabled: false,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('Kickoff: renders OutputFieldContent as wrapper for options', () => {
    render(<ExtraFieldRadio {...baseKickoffProps} />);

    expect(screen.getByTestId('output-field-content')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to OutputFieldContent', () => {
    render(<ExtraFieldRadio {...baseKickoffProps} />);

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
    render(
      <ExtraFieldRadio
        {...baseKickoffProps}
        field={processRunField}
        mode={EExtraFieldMode.ProcessRun}
      />,
    );

    const mock = RadioButton as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(3);
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Red' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Blue' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Green' }), {});
  });

  describe('label-left support', () => {
    it('Kickoff + labelPosition=Left: renders FieldLabel', () => {
      render(<ExtraFieldRadio {...baseKickoffProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
      expect(fieldLabelMock).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Color',
          mode: EExtraFieldMode.Kickoff,
        }),
        {},
      );
    });

    it('Kickoff + labelPosition=Top: no FieldLabel', () => {
      render(<ExtraFieldRadio {...baseKickoffProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
    });

    it('Kickoff + labelPosition=Left: passes className with label-left to OutputFieldContent', () => {
      render(<ExtraFieldRadio {...baseKickoffProps} labelPosition={EFieldLabelPosition.Left} />);

      const mock = OutputFieldContent as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(1);
      expect(mock).toHaveBeenCalledWith(
        expect.objectContaining({
          className: expect.stringContaining('label-left'),
        }),
        {},
      );
    });

    it('ProcessRun + labelPosition=Left: renders FieldLabel with aligned-start class', () => {
      render(
        <ExtraFieldRadio
          {...baseKickoffProps}
          field={processRunField}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Left}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
      expect(fieldLabelMock).toHaveBeenCalledWith(
        expect.objectContaining({
          className: expect.stringContaining('aligned-start'),
        }),
        {},
      );
    });

    it('ProcessRun + labelPosition=Top: renders static name div, no FieldLabel', () => {
      render(
        <ExtraFieldRadio
          {...baseKickoffProps}
          field={processRunField}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Top}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('Color')).toBeInTheDocument();
    });
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
        labelPosition: EFieldLabelPosition.Top,
      };

      render(<ExtraFieldRadio {...commonProps} field={field1} />);
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

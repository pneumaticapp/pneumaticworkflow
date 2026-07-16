import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldCheckbox } from '../ExtraFieldCheckbox';
import { OutputFieldContent } from '../../utils/OutputFieldContent';
import { FieldLabel } from '../../utils/FieldLabel';
import { Checkbox } from '../../../../UI/Fields/Checkbox';
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

jest.mock('../../../../UI/Fields/Checkbox', () => ({
  Checkbox: jest.fn(({ title }: { title: string }) =>
    React.createElement('span', { 'data-testid': `checkbox-${title}` }, title),
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

describe('ExtraFieldCheckbox', () => {
  const mockEditField = jest.fn();

  const kickoffSelections: IExtraFieldSelection[] = [
    { key: 1, value: 'Red', isSelected: false, apiName: 'opt-1' },
    { key: 2, value: 'Blue', isSelected: false, apiName: 'opt-2' },
  ];

  const processRunSelections = ['Red', 'Blue', 'Green'];

  const kickoffField = makeExtraField({
    name: 'Colors',
    type: EExtraFieldType.Checkbox,
    selections: kickoffSelections,
  });

  const processRunField = makeExtraField({
    name: 'Colors',
    type: EExtraFieldType.Checkbox,
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
    render(<ExtraFieldCheckbox {...baseKickoffProps} />);

    expect(screen.getByTestId('output-field-content')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to OutputFieldContent', () => {
    render(<ExtraFieldCheckbox {...baseKickoffProps} />);

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
    render(
      <ExtraFieldCheckbox
        {...baseKickoffProps}
        field={processRunField}
        mode={EExtraFieldMode.ProcessRun}
      />,
    );

    const mock = Checkbox as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(3);
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Red' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Blue' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ title: 'Green' }), {});
  });

  describe('label-left support', () => {
    it('Kickoff + labelPosition=Left: renders FieldLabel', () => {
      render(<ExtraFieldCheckbox {...baseKickoffProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
    });

    it('Kickoff + labelPosition=Top: no FieldLabel', () => {
      render(<ExtraFieldCheckbox {...baseKickoffProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
    });

    it('Kickoff + labelPosition=Left: passes className with label-left to OutputFieldContent', () => {
      render(<ExtraFieldCheckbox {...baseKickoffProps} labelPosition={EFieldLabelPosition.Left} />);

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
        <ExtraFieldCheckbox
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
        <ExtraFieldCheckbox
          {...baseKickoffProps}
          field={processRunField}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Top}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('Colors')).toBeInTheDocument();
    });
  });
});

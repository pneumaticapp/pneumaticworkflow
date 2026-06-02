/**
 * ExtraFieldCreatable — компонент dropdown-поля.
 * Тип: ExtraField с двумя режимами (Kickoff / ProcessRun).
 * Путь: ExtraFields/Creatable/ExtraFieldCreatable.tsx
 *
 * Контракт label-left:
 * - Kickoff + Left → FieldWithName получает labelClassName с _centered
 * - Kickoff + Top → labelClassName НЕ передаётся
 * - Kickoff + Left → options обёрнуты в wrapper с _label-left
 * - ProcessRun + Left → FieldLabel с _centered классом
 * - ProcessRun + Top → static name div, FieldLabel не рендерится
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldCreatable } from '../ExtraFieldCreatable';
import { OutputFieldContent } from '../../utils/OutputFieldContent';
import { FieldLabel } from '../../utils/FieldLabel';
import { DropdownList } from '../../../../UI/DropdownList';
import { IWorkflowExtraFieldProps } from '../../types';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldMode, EExtraFieldType, IExtraFieldSelection } from '../../../../../types/template';
import { EFieldLabelPosition } from '../../../../../types/fieldset';

// --- Мок конфигурации ---

jest.mock('../../utils/OutputFieldContent', () => ({
  OutputFieldContent: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'output-field-content' }, children),
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

// FieldWithName — prop-drilling мок (правило 42)
jest.mock('../../utils/FieldWithName', () => {
  const React = require('react');
  return {
    FieldWithName: jest.fn(() => React.createElement('div', { 'data-testid': 'field-with-name' })),
  };
});

// FieldLabel — prop-drilling мок (правило 42)
jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

jest.mock('../../../KickoffRedux/utils/getEmptySelection', () => ({
  getEmptySelection: jest.fn(() => ({ id: 'empty', value: '', isSelected: false, apiName: 'empty' })),
}));

// --- Тесты ---

describe('ExtraFieldCreatable', () => {
  const mockEditField = jest.fn();

  // Получаем мок FieldWithName через require (ForwardRef → jest.Mock каст невозможен)
  const getFieldWithNameMock = (): jest.Mock =>
    require('../../utils/FieldWithName').FieldWithName;

  const kickoffSelections: IExtraFieldSelection[] = [
    { key: 1, value: 'High', isSelected: false, apiName: 'opt-1' },
    { key: 2, value: 'Low', isSelected: false, apiName: 'opt-2' },
  ];

  const processRunSelections = ['High', 'Medium', 'Low'];

  const kickoffField = makeExtraField({
    name: 'Priority',
    type: EExtraFieldType.Creatable,
    description: 'Select priority',
    selections: kickoffSelections,
  });

  const processRunField = makeExtraField({
    name: 'Priority',
    type: EExtraFieldType.Creatable,
    selections: processRunSelections,
    value: 'High',
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

  // --- Существующие тесты (переписаны без any) ---

  it('Kickoff: renders OutputFieldContent as wrapper for options', () => {
    render(<ExtraFieldCreatable {...baseKickoffProps} />);

    expect(screen.getByTestId('output-field-content')).toBeInTheDocument();
  });

  it('Kickoff: passes field, editField, isDisabled to OutputFieldContent', () => {
    render(<ExtraFieldCreatable {...baseKickoffProps} />);

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

  it('ProcessRun: renders DropdownList with string selections as options', () => {
    render(
      <ExtraFieldCreatable
        {...baseKickoffProps}
        field={processRunField}
        mode={EExtraFieldMode.ProcessRun}
      />,
    );

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

  // --- label-left ветвления ---
  // Kickoff делегирует через FieldWithName, ProcessRun использует FieldLabel напрямую

  describe('label-left support', () => {
    // Kickoff + Left → FieldWithName получает labelClassName с centered
    it('Kickoff + labelPosition=Left: passes labelClassName with centered class to FieldWithName', () => {
      render(<ExtraFieldCreatable {...baseKickoffProps} labelPosition={EFieldLabelPosition.Left} />);

      const mock = getFieldWithNameMock();
      expect(mock).toHaveBeenCalledTimes(1);
      expect(mock).toHaveBeenCalledWith(
        expect.objectContaining({
          labelClassName: expect.stringContaining('centered'),
        }),
        {},
      );
    });

    // Kickoff + Top → FieldWithName без labelClassName
    it('Kickoff + labelPosition=Top: does NOT pass labelClassName to FieldWithName', () => {
      render(<ExtraFieldCreatable {...baseKickoffProps} labelPosition={EFieldLabelPosition.Top} />);

      const mock = getFieldWithNameMock();
      expect(mock).toHaveBeenCalledTimes(1);
      expect(mock).toHaveBeenCalledWith(
        expect.not.objectContaining({ labelClassName: expect.anything() }),
        {},
      );
    });

    // ProcessRun + Left → FieldLabel с centered классом
    it('ProcessRun + labelPosition=Left: renders FieldLabel with centered class', () => {
      render(
        <ExtraFieldCreatable
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
          className: expect.stringContaining('centered'),
        }),
        {},
      );
    });

    // ProcessRun + Top → readonly name div, FieldLabel не вызван
    it('ProcessRun + labelPosition=Top: renders readonly name div, no FieldLabel', () => {
      render(
        <ExtraFieldCreatable
          {...baseKickoffProps}
          field={processRunField}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Top}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('Priority')).toBeInTheDocument();
    });
  });
});

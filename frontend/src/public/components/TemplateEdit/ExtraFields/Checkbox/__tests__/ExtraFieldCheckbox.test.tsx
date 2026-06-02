/**
 * ExtraFieldCheckbox — компонент чекбокс-поля.
 * Тип: ExtraField с двумя режимами (Kickoff / ProcessRun).
 * Путь: ExtraFields/Checkbox/ExtraFieldCheckbox.tsx
 *
 * Контракт:
 * - Kickoff → OutputFieldContent с опциями-чекбоксами (IExtraFieldSelection[])
 * - ProcessRun → Checkbox для каждой строки из selections
 * - labelPosition=Left → FieldLabel, className с label-left на OutputFieldContent
 * - labelPosition=Top → inline textarea, нет FieldLabel
 */
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

// --- Мок конфигурации ---

// OutputFieldContent — интерактивный, рендерит children (правило 41)
jest.mock('../../utils/OutputFieldContent', () => ({
  OutputFieldContent: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'output-field-content' }, children),
  ),
}));

// Checkbox — интерактивный мок, рендерит title для проверки (правило 41)
jest.mock('../../../../UI/Fields/Checkbox', () => ({
  Checkbox: jest.fn(({ title }: { title: string }) =>
    React.createElement('span', { 'data-testid': `checkbox-${title}` }, title),
  ),
}));

// react-input-autosize — интерактивный мок (правило 41)
jest.mock('react-input-autosize', () => ({
  __esModule: true,
  default: jest.fn(({ value, onChange, placeholder }: { value: string; onChange: () => void; placeholder: string }) =>
    React.createElement('input', { value: value || '', onChange, placeholder }),
  ),
}));

// Иконки — barrel, мокаем целиком (правило 36)
jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
  RemoveIcon: () => null,
}));

// Утилиты
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

// FieldLabel — prop-drilling мок (правило 42)
jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

// --- Тесты ---

describe('ExtraFieldCheckbox', () => {
  const mockEditField = jest.fn();

  // Kickoff selections — объектный формат IExtraFieldSelection[]
  const kickoffSelections: IExtraFieldSelection[] = [
    { key: 1, value: 'Red', isSelected: false, apiName: 'opt-1' },
    { key: 2, value: 'Blue', isSelected: false, apiName: 'opt-2' },
  ];

  // ProcessRun selections — строковый формат string[]
  const processRunSelections = ['Red', 'Blue', 'Green'];

  // Правило 48: используем makeExtraField
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

  // Типизированные пропсы без any
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

  // --- Основной функционал ---

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

  // --- label-left ветвления ---
  // Проверяем переключение между FieldLabel и inline textarea по labelPosition

  describe('label-left support', () => {
    // Kickoff + Left → FieldLabel рендерится
    it('Kickoff + labelPosition=Left: renders FieldLabel', () => {
      render(<ExtraFieldCheckbox {...baseKickoffProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
    });

    // Kickoff + Top → FieldLabel не вызван
    it('Kickoff + labelPosition=Top: no FieldLabel', () => {
      render(<ExtraFieldCheckbox {...baseKickoffProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
    });

    // Kickoff + Left → OutputFieldContent получает className с label-left
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

    // ProcessRun + Left → FieldLabel с aligned-start
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

    // ProcessRun + Top → статический div с именем
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

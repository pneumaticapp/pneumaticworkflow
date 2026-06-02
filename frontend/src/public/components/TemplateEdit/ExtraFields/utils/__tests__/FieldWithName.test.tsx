/**
 * FieldWithName — wrapper-компонент: объединяет FieldLabel (имя поля) и Field (значение/описание).
 * Тип: wrapper / prop-drilling.
 * Путь: ExtraFields/utils/FieldWithName.tsx
 *
 * Контракт (изменённое поведение):
 * - labelPosition=Left → CSS-класс kick-off-input__field_label-left на контейнере
 * - labelPosition=Top → без этого класса
 * - labelClassName пробрасывается в FieldLabel.className через conditional spread
 * - В Kickoff mode → Field получает description, в ProcessRun → value
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { FieldWithName } from '../FieldWithName';
import { FieldLabel } from '../FieldLabel';
import { Field } from '../../../../Field';
import { EExtraFieldMode } from '../../../../../types/template';
import { EFieldLabelPosition } from '../../../../../types/fieldset';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';

// --- Мок конфигурации ---

// FieldLabel — prop-drilling мок, не нужно рендерить реальный DOM (правило 42)
jest.mock('../FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

// Field — prop-drilling мок
jest.mock('../../../../Field', () => ({
  Field: jest.fn(() => null),
  EFieldTagName: {},
}));

// Валидаторы
jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

// --- Тесты ---

describe('FieldWithName', () => {
  const mockHandleChangeName = jest.fn();
  const mockHandleChangeDescription = jest.fn();
  const mockValidate = jest.fn(() => '');

  // Базовые пропсы — правило 48: используем фабрику makeExtraField
  const baseProps = {
    field: makeExtraField({ name: 'Test', description: 'Desc text', value: 'Val text' }),
    handleChangeName: mockHandleChangeName,
    handleChangeDescription: mockHandleChangeDescription,
    validate: mockValidate,
    isDisabled: false,
    labelPosition: EFieldLabelPosition.Top,
    mode: EExtraFieldMode.Kickoff,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // --- labelPosition → CSS-класс на контейнере ---
  // Ключевое изменение PR: контейнер получает класс _label-left при labelPosition=Left

  describe('labelPosition → CSS class', () => {
    // Top → без класса label-left
    it('labelPosition=Top: container does NOT get label-left class', () => {
      render(React.createElement(FieldWithName, baseProps));

      const container = screen.getByLabelText('field-container');
      expect(container.className).not.toContain('label-left');
    });

    // Left → с классом label-left
    it('labelPosition=Left: container gets label-left class', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          labelPosition: EFieldLabelPosition.Left,
        }),
      );

      const container = screen.getByLabelText('field-container');
      expect(container.className).toContain('label-left');
    });
  });

  // --- labelClassName → FieldLabel ---
  // Conditional spread: {...(labelClassName && { className: labelClassName })}

  describe('labelClassName → FieldLabel', () => {
    // Когда передан → FieldLabel получает className
    it('passes labelClassName to FieldLabel when provided', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          labelClassName: 'custom-label-class',
        }),
      );

      const mock = FieldLabel as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(1);
      expect(mock).toHaveBeenCalledWith(
        expect.objectContaining({ className: 'custom-label-class' }),
        {},
      );
    });

    // Когда не передан → FieldLabel НЕ получает className
    it('does NOT pass className to FieldLabel when labelClassName is undefined', () => {
      render(React.createElement(FieldWithName, baseProps));

      const mock = FieldLabel as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(1);
      const calledProps = mock.mock.calls[0][0];
      expect(calledProps).not.toHaveProperty('className');
    });
  });

  // --- description vs value по mode ---
  // В Kickoff → description, в ProcessRun → value (из field)

  describe('description field value by mode', () => {
    // Kickoff → Field получает description
    it('uses description in Kickoff mode', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          mode: EExtraFieldMode.Kickoff,
        }),
      );

      const fieldMock = Field as jest.Mock;
      expect(fieldMock).toHaveBeenCalledTimes(1);
      expect(fieldMock).toHaveBeenCalledWith(
        expect.objectContaining({ value: 'Desc text' }),
        {},
      );
    });

    // ProcessRun → Field получает value
    it('uses value in ProcessRun mode', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          mode: EExtraFieldMode.ProcessRun,
        }),
      );

      const fieldMock = Field as jest.Mock;
      expect(fieldMock).toHaveBeenCalledTimes(1);
      expect(fieldMock).toHaveBeenCalledWith(
        expect.objectContaining({ value: 'Val text' }),
        {},
      );
    });
  });
});

/**
 * FieldLabel — компонент лейбла для поля ввода.
 * Тип: UI-компонент с двумя режимами отображения.
 * Путь: ExtraFields/utils/FieldLabel.tsx
 *
 * Контракт:
 * - mode=Kickoff → редактируемый TextareaAutosize + кнопка-карандаш + знак обязательности
 * - mode≠Kickoff → readonly div с текстом имени + знак обязательности
 * - Кнопка-карандаш скрывается при фокусе на textarea
 * - handleChangeName вызывается при вводе в textarea
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldLabel, IFieldLabelProps } from '../FieldLabel';
import { EExtraFieldMode } from '../../../../../types/template';

// --- Мок конфигурации ---

// TextareaAutosize — интерактивный мок, ОБЯЗАН рендерить реальный <textarea> (правило 41)
// Используем forwardRef т.к. компонент использует ref (правило 35)
// jest.fn() создаётся ВНУТРИ фабрики (правило 33 — хоистинг)
jest.mock('react-textarea-autosize', () => {
  const ReactInsideMock = require('react');

  return {
    __esModule: true,
    default: ReactInsideMock.forwardRef(
      (
        props: {
          value: string;
          onChange: React.ChangeEventHandler<HTMLTextAreaElement>;
          placeholder: string;
          disabled: boolean;
          onFocus: () => void;
          onBlur: () => void;
        },
        ref: React.Ref<HTMLTextAreaElement>,
      ) =>
        ReactInsideMock.createElement('textarea', {
          value: props.value || '',
          onChange: props.onChange,
          placeholder: props.placeholder,
          disabled: props.disabled,
          onFocus: props.onFocus,
          onBlur: props.onBlur,
          ref,
          'aria-label': 'field name',
        }),
    ),
  };
});

// Иконки — barrel, мокаем целиком (правило 36)
jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
}));

// Утилиты
jest.mock('../getInputNameBackground', () => ({
  getInputNameBackground: jest.fn(() => ''),
}));

jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

// --- Тесты ---

describe('FieldLabel', () => {
  const mockHandleChangeName = jest.fn();

  // Базовые пропсы без mode — каждый тест передаёт mode явно
  const baseProps: Omit<IFieldLabelProps, 'mode'> = {
    name: 'My field',
    isRequired: false,
    isDisabled: false,
    handleChangeName: mockHandleChangeName,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // --- Kickoff mode: редактируемый лейбл ---
  // Проверяем что в Kickoff рендерится textarea, знак обязательности, кнопка-карандаш и callback

  describe('Kickoff mode', () => {
    const kickoffProps: IFieldLabelProps = { ...baseProps, mode: EExtraFieldMode.Kickoff };

    // Основной рендер — textarea с value поля
    it('renders editable textarea with field name', () => {
      render(<FieldLabel {...kickoffProps} />);

      const textarea = screen.getByRole('textbox', { name: 'field name' });
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('My field');
    });

    // Булев флаг isRequired=true → знак обязательности в DOM
    it('renders required sign when isRequired=true', () => {
      render(<FieldLabel {...kickoffProps} isRequired={true} />);

      expect(screen.getByLabelText('required')).toBeInTheDocument();
    });

    // Булев флаг isRequired=false → знак обязательности отсутствует
    it('hides required sign when isRequired=false', () => {
      render(<FieldLabel {...kickoffProps} isRequired={false} />);

      expect(screen.queryByLabelText('required')).not.toBeInTheDocument();
    });

    // Кнопка-карандаш видна когда textarea не в фокусе
    it('renders edit button when textarea is not focused', () => {
      render(<FieldLabel {...kickoffProps} />);

      expect(screen.getByRole('button', { name: 'Edit field name' })).toBeInTheDocument();
    });

    // Кнопка-карандаш скрывается при фокусе — защищает логику isFocused state
    it('hides edit button when textarea is focused', () => {
      render(<FieldLabel {...kickoffProps} />);

      const textarea = screen.getByRole('textbox', { name: 'field name' });
      userEvent.click(textarea);

      expect(screen.queryByRole('button', { name: 'Edit field name' })).not.toBeInTheDocument();
    });

    // Callback — ввод символа вызывает handleChangeName
    it('calls handleChangeName on textarea input', () => {
      render(<FieldLabel {...kickoffProps} />);

      const textarea = screen.getByRole('textbox', { name: 'field name' });
      userEvent.type(textarea, 'X');

      expect(mockHandleChangeName).toHaveBeenCalledTimes(1);
    });
  });

  // --- Non-kickoff mode: readonly лейбл ---
  // Проверяем что НЕ рендерится textarea, а рендерится readonly div

  describe('Non-kickoff mode', () => {
    const processRunProps: IFieldLabelProps = { ...baseProps, mode: EExtraFieldMode.ProcessRun };

    // Текст имени в readonly div, textarea отсутствует
    it('renders readonly name text', () => {
      render(<FieldLabel {...processRunProps} />);

      expect(screen.getByText('My field')).toBeInTheDocument();
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    // Булев флаг isRequired=true → знак обязательности
    it('renders required sign when isRequired=true', () => {
      render(<FieldLabel {...processRunProps} isRequired={true} />);

      expect(screen.getByLabelText('required')).toBeInTheDocument();
    });

    // Булев флаг isRequired=false → нет знака обязательности
    it('hides required sign when isRequired=false', () => {
      render(<FieldLabel {...processRunProps} isRequired={false} />);

      expect(screen.queryByLabelText('required')).not.toBeInTheDocument();
    });
  });
});

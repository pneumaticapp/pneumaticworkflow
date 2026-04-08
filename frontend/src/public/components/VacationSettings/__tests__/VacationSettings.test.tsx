// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../__stubs__/intlMock';
import { VacationSettings } from '../VacationSettings';

jest.mock('../../UI/Fields/DateField', () => ({
  DateField: ({ value, onChange, title }: any) => (
    <div>
      <label>{title}</label>
      <input
        type="date"
        aria-label={title}
        value={value || ''}
        onChange={(e) => {
          const parts = e.target.value.split('-');
          if (parts.length === 3) {
            onChange(new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])));
          } else {
            onChange(null);
          }
        }}
      />
    </div>
  ),
}));

jest.mock('../../UI/form/UsersDropdown', () => ({
  EOptionTypes: { User: 'user' },
  UsersDropdown: ({ options, onChange }: any) => (
    <div data-testid="users-dropdown">
      {options.map((opt: any) => (
        <button
          key={opt.value}
          data-testid={`select-user-${opt.value}`}
          onClick={() => onChange(opt)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock('../../UI/UserPerformer', () => ({
  UserPerformer: ({ user, onClick }: any) => (
    <button data-testid={`remove-user-${user.value}`} onClick={onClick}>
      Remove {user.label}
    </button>
  ),
  EBgColorTypes: { Light: 'light' },
}));

jest.mock('../../UI/DropdownList', () => ({
  DropdownList: ({ options, value, onChange, label }: any) => (
    <div data-testid="status-dropdown">
      <span>{label}</span>
      {options.map((opt: any) => (
        <button
          key={opt.value}
          data-testid={`status-${opt.value}`}
          className={value && value.value === opt.value ? 'active' : ''}
          onClick={() => onChange(opt)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock('../../UI/Buttons/Button', () => ({
  Button: jest.fn(({ label, onClick, disabled, ...rest }: any) => (
    <button onClick={onClick} disabled={disabled} data-testid={rest['data-testid']}>
      {label}
    </button>
  )),
}));

jest.mock('../../UI/Typeography/Header', () => ({
  Header: jest.fn(({ children }: any) => <h2 data-testid="header">{children}</h2>),
}));

describe('VacationSettings', () => {
  const mockOnActivate = jest.fn();
  const mockOnDeactivate = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  const TITLE = t('user-info.vacation.title');

  const ACTIVE_MSG = t('user-info.vacation.active');


  const makeUser = (overrides: Record<string, unknown> = {}) => ({
    id: 10,
    firstName: 'Alice',
    lastName: 'Smith',
    ...overrides,
  });

  const baseProps = {
    isAbsent: false,
    absenceStatus: 'vacation',
    vacationStartDate: null as string | null,
    vacationEndDate: null as string | null,
    substituteUserIds: [] as number[],
    availableUsers: [
      makeUser({ id: 10 }),
      makeUser({ id: 20, firstName: 'Bob', lastName: 'Jones' }),
    ] as any[],
    onActivate: mockOnActivate,
    onDeactivate: mockOnDeactivate,
    isLoading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('displays the title', () => {
      render(<VacationSettings {...baseProps} />);
      expect(screen.getByTestId('header')).toHaveTextContent(TITLE);
    });

    it('selects active status by default when not absent', () => {
      render(<VacationSettings {...baseProps} />);
      expect(screen.getByTestId('status-active')).toHaveClass('active');
      expect(screen.queryByTestId('vacation-start-input')).not.toBeInTheDocument();
    });

    it('selects vacation status by default when absent', () => {
      render(<VacationSettings {...baseProps} isAbsent />);
      expect(screen.getByTestId('status-vacation')).toHaveClass('active');
      expect(screen.getByTestId('vacation-start-input')).toBeInTheDocument();
    });
  });

  describe('Activation', () => {
    it('allows activating vacation with dates and substitutes', () => {
      render(<VacationSettings {...baseProps} />);

      // Switch to vacation
      userEvent.click(screen.getByTestId('status-vacation'));

      // Set dates
      const startInput = screen.getByTestId('vacation-start-input').querySelector('input')!;
      const endInput = screen.getByTestId('vacation-end-input').querySelector('input')!;
      userEvent.clear(startInput);
      userEvent.type(startInput, '2026-04-01');
      userEvent.clear(endInput);
      userEvent.type(endInput, '2026-04-15');

      // Select substitutes
      userEvent.click(screen.getByTestId('select-user-10'));
      userEvent.click(screen.getByTestId('select-user-20'));

      // Submit
      userEvent.click(screen.getByTestId('vacation-activate-btn'));

      expect(mockOnActivate).toHaveBeenCalledWith({
        absenceStatus: 'vacation',
        substituteUserIds: [10, 20],
        vacationStartDate: '2026-04-01',
        vacationEndDate: '2026-04-15',
      });
    });

    it('does not submit the form without substitutes', () => {
      render(<VacationSettings {...baseProps} />);

      userEvent.click(screen.getByTestId('status-vacation'));
      userEvent.click(screen.getByTestId('vacation-activate-btn'));

      expect(mockOnActivate).not.toHaveBeenCalled();
    });
  });

  describe('Deactivation', () => {
    it('allows deactivating when absent and active is selected', () => {
      render(<VacationSettings {...baseProps} isAbsent />);

      // Switch to active
      userEvent.click(screen.getByTestId('status-active'));
      expect(screen.getByText(ACTIVE_MSG)).toBeInTheDocument();

      userEvent.click(screen.getByTestId('vacation-deactivate-btn'));
      expect(mockOnDeactivate).toHaveBeenCalled();
    });
  });

  describe('Substitute management', () => {
    it('removes a substitute on click', () => {
      render(<VacationSettings {...baseProps} />);
      userEvent.click(screen.getByTestId('status-vacation'));

      // Add two substitutes
      userEvent.click(screen.getByTestId('select-user-10'));
      userEvent.click(screen.getByTestId('select-user-20'));

      // Remove one
      userEvent.click(screen.getByTestId('remove-user-10'));

      userEvent.click(screen.getByTestId('vacation-activate-btn'));

      expect(mockOnActivate).toHaveBeenCalledWith(
        expect.objectContaining({ substituteUserIds: [20] }),
      );
    });
  });
});

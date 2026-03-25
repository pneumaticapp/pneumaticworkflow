import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

import { intlMock } from '../../../__stubs__/intlMock';
import { VacationSettings } from '../VacationSettings';

jest.mock('../../UI/Fields/DateField', () => ({
  DateField: ({ value, onChange, 'data-testid': testId }: any) => (
    <input
      type="date"
      data-testid={testId || 'date-field'}
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

jest.mock('../../UserDataWithGroup', () => ({
  __esModule: true,
  default: ({ children, idItem }: any) => (
    <div data-testid={`user-data-wrapper-${idItem}`}>
      {children({ id: idItem, firstName: 'Mock', lastName: 'User' })}
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

jest.mock('../../UI/Tabs', () => ({
  Tabs: ({ values, activeValueId, onChange }: any) => (
    <div data-testid="tabs">
      {values.map((val: any) => (
        <button
          key={val.id}
          data-testid={`tab-${val.id}`}
          className={activeValueId === val.id ? 'active' : ''}
          onClick={() => onChange(val.id)}
        >
          {val.label}
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

  it('renders header', () => {
    render(<VacationSettings {...baseProps} />);
    expect(screen.getByTestId('header')).toHaveTextContent(intlMock.formatMessage({ id: 'user-info.vacation.title' }));
  });

  it('renders tabs and defaults to active if not absent', () => {
    render(<VacationSettings {...baseProps} />);
    expect(screen.getByTestId('tab-active')).toHaveClass('active');
    expect(screen.queryByTestId('vacation-start-input')).not.toBeInTheDocument();
  });

  it('defaults to vacation if absent', () => {
    render(<VacationSettings {...baseProps} isAbsent={true} />);
    expect(screen.getByTestId('tab-vacation')).toHaveClass('active');
    expect(screen.getByTestId('vacation-start-input')).toBeInTheDocument();
  });

  it('allows activating vacation with dates and substitutes', () => {
    render(<VacationSettings {...baseProps} />);
    
    // Switch to vacation tab
    fireEvent.click(screen.getByTestId('tab-vacation'));
    
    // Set dates
    const startInput = screen.getByTestId('vacation-start-input').querySelector('input')!;
    const endInput = screen.getByTestId('vacation-end-input').querySelector('input')!;
    
    fireEvent.change(startInput, { target: { value: '2026-04-01' } });
    fireEvent.change(endInput, { target: { value: '2026-04-15' } });

    // Select user
    fireEvent.click(screen.getByTestId('select-user-10'));
    fireEvent.click(screen.getByTestId('select-user-20'));

    // Submit
    fireEvent.click(screen.getByTestId('vacation-activate-btn'));

    expect(mockOnActivate).toHaveBeenCalledWith({
      absenceStatus: 'vacation',
      substituteUserIds: [10, 20],
      vacationStartDate: '2026-04-01',
      vacationEndDate: '2026-04-15',
    });
  });

  it('allows deactivating if absent and active tab is selected', () => {
    render(<VacationSettings {...baseProps} isAbsent={true} />);
    
    // Switch to active tab
    fireEvent.click(screen.getByTestId('tab-active'));
    expect(screen.getByText(intlMock.formatMessage({ id: 'user-info.vacation.active' }))).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('vacation-deactivate-btn'));
    expect(mockOnDeactivate).toHaveBeenCalled();
  });

  it('removes substitute user properly', () => {
    render(<VacationSettings {...baseProps} />);
    fireEvent.click(screen.getByTestId('tab-vacation'));
    
    // Add both
    fireEvent.click(screen.getByTestId('select-user-10'));
    fireEvent.click(screen.getByTestId('select-user-20'));
    
    // Remove one
    fireEvent.click(screen.getByTestId('remove-user-10'));
    
    fireEvent.click(screen.getByTestId('vacation-activate-btn'));

    expect(mockOnActivate).toHaveBeenCalledWith(expect.objectContaining({ substituteUserIds: [20] }));
  });
});

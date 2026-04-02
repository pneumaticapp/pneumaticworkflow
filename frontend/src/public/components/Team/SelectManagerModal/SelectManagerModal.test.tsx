// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector, useDispatch } from 'react-redux';

import { SelectManagerModal } from './SelectManagerModal';
import { UsersDropdownComponent } from '../../UI/form/UsersDropdown/UsersDropdown';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
  useDispatch: jest.fn(),
}));

jest.mock('react-intl', () => ({
  useIntl: () => ({
    formatMessage: ({ id }: { id: string }) => id,
  }),
}));

jest.mock('../../UI', () => ({
  Modal: ({ children, isOpen }: any) => (isOpen ? <div data-testid="modal">{children}</div> : null),
  Button: ({ onClick, label, ...props }: any) => (
    <button onClick={onClick} data-testid={`btn-${label}`} {...props}>
      {label}
    </button>
  ),
}));

jest.mock('../../UI/form/UsersDropdown/UsersDropdown', () => ({
  UsersDropdownComponent: jest.fn(() => <div data-testid="users-dropdown" />),
  EOptionTypes: { User: 'User' },
}));

const makeUser = (overrides: any = {}) => ({
  id: 1,
  firstName: 'John',
  lastName: 'Doe',
  email: 'john@example.com',
  isDeleted: false,
  ...overrides,
});

describe('SelectManagerModal', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();
  const mockDispatch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockReturnValue([
      makeUser({ id: 1, firstName: 'Current', lastName: 'User' }),
      makeUser({ id: 2, firstName: 'Potential', lastName: 'Manager' }),
      makeUser({ id: 3, firstName: 'Another', lastName: 'Manager' }),
    ]);
  });

  describe('Рендер', () => {
    it('не отображает модалку, если isOpen=false', () => {
      // arrange & act
      render(
        <SelectManagerModal
          isOpen={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          currentManagerId={null}
          currentUserId={1}
        />
      );

      // assert
      expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });

    it('отображает кнопку Remove, если есть currentManagerId', () => {
      // arrange & act
      render(
        <SelectManagerModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          currentManagerId={2}
          currentUserId={1}
        />
      );

      // assert
      expect(screen.getByTestId('btn-button.remove')).toBeInTheDocument();
    });

    it('не отображает кнопку Remove, если currentManagerId=null', () => {
      // arrange & act
      render(
        <SelectManagerModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          currentManagerId={null}
          currentUserId={1}
        />
      );

      // assert
      expect(screen.queryByTestId('btn-button.remove')).not.toBeInTheDocument();
    });
  });

  describe('Действия', () => {
    it('вызывает onConfirm с null при клике на Remove', () => {
      // arrange
      render(
        <SelectManagerModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          currentManagerId={2}
          currentUserId={1}
        />
      );

      // act
      userEvent.click(screen.getByTestId('btn-button.remove'));

      // assert
      expect(mockOnConfirm).toHaveBeenCalledWith(null);
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('фильтрует текущего пользователя из списка доступных менеджеров', () => {
      // arrange & act
      render(
        <SelectManagerModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          currentManagerId={null}
          currentUserId={1} // The current user
        />
      );

      // assert
      // UsersDropdownComponent props options should not contain user id=1
      const dropdownProps = (UsersDropdownComponent as jest.Mock).mock.calls[0][0];
      const optionIds = dropdownProps.options.map((o: any) => o.value);
      expect(optionIds).not.toContain('1');
      expect(optionIds).toContain('2');
      expect(optionIds).toContain('3');
    });

    it('вызывает onConfirm с ID выбранного менеджера при клике на Save', () => {
      // arrange
      render(
        <SelectManagerModal
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          currentManagerId={null}
          currentUserId={1}
        />
      );
      
      // Simulate selecting a manager
      const dropdownProps = (UsersDropdownComponent as jest.Mock).mock.calls[0][0];
      dropdownProps.onChange({ value: '3', id: 3, label: 'Another Manager' });

      // act
      userEvent.click(screen.getByTestId('btn-Save'));

      // assert
      expect(mockOnConfirm).toHaveBeenCalledWith(3);
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});

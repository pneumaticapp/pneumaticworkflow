/// <reference types="jest" />
import * as React from 'react';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { CreateUserModal } from '../CreateUserModal';
import { createUser } from '../../../../../redux/accounts/slice';
import { NotificationManager } from '../../../../UI/Notifications';
import { copyToClipboard } from '../../../../../utils/helpers';
import { createPassword } from '../../../../../utils/createPassword';
import { intlMock } from '../../../../../__stubs__/intlMock';

jest.mock('react-dom', () => {
  const actualReactDOM = jest.requireActual('react-dom');
  
  return {
    ...actualReactDOM,
    default: {
      ...actualReactDOM.default,
      createPortal: (element: React.ReactNode) => element,
    },
  };
});

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
}));

jest.mock('../../../../../redux/accounts/slice', () => ({
  createUser: jest.fn((payload) => ({ type: 'accounts/createUser', payload })),
}));

jest.mock('../../../../UI/Notifications', () => ({
  NotificationManager: {
    success: jest.fn(),
  },
}));

jest.mock('../../../../../utils/helpers', () => ({
  copyToClipboard: jest.fn(),
}));

jest.mock('../../../../../utils/createPassword', () => ({
  createPassword: jest.fn(() => 'mock-password-123'),
}));

jest.mock('react-perfect-scrollbar', () => {
  const MockScrollbar = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  return {
    __esModule: true,
    default: MockScrollbar,
  };
});

describe('CreateUserModal', () => {
  const mockDispatch = jest.fn();
  const mockOnClose = jest.fn();

  const renderModal = async (isOpen = true) => {
    let renderResult: ReturnType<typeof render> | undefined;

    await act(async () => {
      renderResult = render(<CreateUserModal isOpen={isOpen} onClose={mockOnClose} />);
    });

    return renderResult!;
  };

  const setInputValue = async (input: HTMLInputElement, value: string) => {
    await act(async () => {
      fireEvent.change(input, { target: { value } });
    });
  };

  const clickElement = async (element: HTMLElement) => {
    await act(async () => {
      userEvent.click(element);
    });
  };

  const getTranslatedText = (id: string) => intlMock.formatMessage({ id });

  const PASSWORD_COPIED_MESSAGE = 'team.create-user-modal.password-copied';
  const ADMIN_OPTION_TEXT = getTranslatedText('team.create-user-modal.status-admin');
  const USER_OPTION_TEXT = getTranslatedText('team.create-user-modal.status-user');

  const getFormFields = () => ({
    firstNameInput: screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name')) as HTMLInputElement,
    lastNameInput: screen.getByLabelText(getTranslatedText('team.create-user-modal.last-name')) as HTMLInputElement,
    emailInput: screen.getByLabelText(getTranslatedText('team.create-user-modal.email')) as HTMLInputElement,
    passwordInput: screen.getByLabelText(getTranslatedText('team.create-user-modal.password')) as HTMLInputElement,
  });

  const getSubmitButton = () => screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.submit') });

  const getCopyButton = () => screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.copy') });

  const getRoleDropdown = () => {
    const label = screen.getByText(getTranslatedText('team.create-user-modal.status'));
    const dropdownContainer = label.closest('.react-select')!;
    return dropdownContainer.querySelector('.react-select__control') as HTMLElement;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  describe('Rendering', () => {
    it('does not render when isOpen=false', async () => {
      await renderModal(false);

      expect(screen.queryByTestId('create-user-modal-header')).not.toBeInTheDocument();
    });

    it('renders when isOpen=true', async () => {
      await renderModal();

      expect(screen.getByTestId('create-user-modal-header')).toBeInTheDocument();
    });

    it('displays all form fields', async () => {
      await renderModal();

      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.last-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.email'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-user-modal.status'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.password'))).toBeInTheDocument();
    });

    it('displays submit button', async () => {
      await renderModal();

      expect(screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.submit') })).toBeInTheDocument();
    });

    it('displays password copy button', async () => {
      await renderModal();

      expect(screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.copy') })).toBeInTheDocument();
    });
  });

  describe('Form validation', () => {
    it('submit button is disabled when form is empty (dirty=false)', async () => {
      await renderModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      expect(firstNameInput.value).toBe('');
      expect(lastNameInput.value).toBe('');
      expect(emailInput.value).toBe('');
      expect(submitButton).toBeDisabled();
    });

    it('submit button is disabled when only one field is filled', async () => {
      await renderModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();

      await setInputValue(firstNameInput, 'John');
      const submitButton = getSubmitButton();

      await waitFor(() => {
        expect(firstNameInput.value).toBe('John');
        expect(lastNameInput.value).toBe('');
        expect(emailInput.value).toBe('');
        expect(submitButton).toBeDisabled();
      });
    });

    it('submit button is disabled with invalid email (dirty=true, isValid=false)', async () => {
      await renderModal();

      const { emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      await setInputValue(emailInput, 'invalid-email');
      await act(async () => {
        fireEvent.blur(emailInput);
      });

      await waitFor(() => {
        expect(emailInput.value).toBe('invalid-email');
        expect(submitButton).toBeDisabled();
      });
    });

    it('submit button is disabled with invalid password (dirty=true, isValid=false due to password)', async () => {
      await renderModal();

      const { passwordInput } = getFormFields();
      const submitButton = getSubmitButton();

      await setInputValue(passwordInput, '12345');
      await act(async () => {
        fireEvent.blur(passwordInput);
      });

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });

    it('submit button is enabled with valid form (dirty=true, isValid=true)', async () => {
      await renderModal();

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      const submitButton = getSubmitButton();

      await setInputValue(firstNameInput, 'John');
      await setInputValue(lastNameInput, 'Doe');
      await setInputValue(emailInput, 'john.doe@example.com');
      await setInputValue(passwordInput, 'valid-password-123');
      await act(async () => {
        fireEvent.blur(passwordInput);
      });

      await waitFor(() => {
        expect(firstNameInput.value).toBe('John');
        expect(lastNameInput.value).toBe('Doe');
        expect(emailInput.value).toBe('john.doe@example.com');
        expect(passwordInput.value).toBe('valid-password-123');
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Password copying', () => {
    it('copies password to clipboard on button click', async () => {
      await renderModal();

      const { passwordInput } = getFormFields();
      const copyButton = getCopyButton();

      await clickElement(copyButton);

      expect(copyToClipboard).toHaveBeenCalledWith(passwordInput.value);
      expect(NotificationManager.success).toHaveBeenCalledWith({
        message: PASSWORD_COPIED_MESSAGE,
      });
    });

    it('copies changed password on button click', async () => {
      await renderModal();

      const { passwordInput } = getFormFields();
      const newPassword = 'my-custom-password-123';

      await setInputValue(passwordInput, newPassword);
      await waitFor(() => {
        expect(passwordInput.value).toBe(newPassword);
      });

      const copyButton = getCopyButton();
      await clickElement(copyButton);

      expect(copyToClipboard).toHaveBeenCalledWith(newPassword);
      expect(NotificationManager.success).toHaveBeenCalledWith({
        message: PASSWORD_COPIED_MESSAGE,
      });
    });
  });

  describe('Form submission', () => {
    it('calls createUser with correct data on submit', async () => {
      await renderModal();

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      const submitButton = getSubmitButton();

      await setInputValue(firstNameInput, 'John');
      await setInputValue(lastNameInput, 'Doe');
      await setInputValue(emailInput, 'john.doe@example.com');

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
      await clickElement(submitButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledWith(
          createUser({
            firstName: 'John',
            lastName: 'Doe',
            email: 'john.doe@example.com',
            password: passwordInput.value,
            isAdmin: false,
          }),
        );
      });
    });

    it('sends isAdmin=true when Admin role is selected', async () => {
      await renderModal();

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();

      await setInputValue(firstNameInput, 'Admin');
      await setInputValue(lastNameInput, 'User');
      await setInputValue(emailInput, 'admin@example.com');

      const roleDropdown = getRoleDropdown();
      await clickElement(roleDropdown);
      const adminOption = await screen.findByText(ADMIN_OPTION_TEXT);
      await clickElement(adminOption);

      const submitButton = getSubmitButton();
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });

      await clickElement(submitButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledWith(
          createUser({
            firstName: 'Admin',
            lastName: 'User',
            email: 'admin@example.com',
            password: passwordInput.value,
            isAdmin: true,
          }),
        );
      });
    });

    it('dispatch is called only once on submit', async () => {
      await renderModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      await setInputValue(firstNameInput, 'John');
      await setInputValue(lastNameInput, 'Doe');
      await setInputValue(emailInput, 'john.doe@example.com');
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });

      await clickElement(submitButton);
      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Form reinitialization', () => {
    it('form resets and password is regenerated on reopen', async () => {
      const { unmount } = await renderModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      await setInputValue(firstNameInput, 'John');
      await setInputValue(lastNameInput, 'Doe');
      await setInputValue(emailInput, 'john.doe@example.com');

      const roleDropdown = getRoleDropdown();
      await clickElement(roleDropdown);
      const adminOption = await screen.findByText(ADMIN_OPTION_TEXT);
      await clickElement(adminOption);

      await waitFor(() => {
        const submitButton = getSubmitButton();
        expect(submitButton).not.toBeDisabled();
      });

      unmount();
      jest.clearAllMocks();

      await renderModal();

      await waitFor(() => {
        expect(createPassword).toHaveBeenCalled();
      });

      await waitFor(() => {
        const { firstNameInput: newFirstNameInput, lastNameInput: newLastNameInput, emailInput: newEmailInput } = getFormFields();
        expect(newFirstNameInput.value).toBe('');
        expect(newLastNameInput.value).toBe('');
        expect(newEmailInput.value).toBe('');
      });

      const submitButton = getSubmitButton();
      expect(submitButton).toBeDisabled();
      const roleDropdownAfterReset = getRoleDropdown();
      expect(roleDropdownAfterReset).toHaveTextContent(USER_OPTION_TEXT);
    });
  });

  describe('Modal closing', () => {
    it('calls onClose on close', async () => {
      await renderModal();
      const closeButtons = screen.getAllByRole('button', { name: 'Close modal' });
      const headerCloseButton = closeButtons.find((button) => button.classList.contains('close-button'));
      expect(headerCloseButton).toBeInTheDocument();
      await clickElement(headerCloseButton!);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});

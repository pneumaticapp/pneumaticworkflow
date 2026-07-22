import * as React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
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

  const openAIAgentTab = async () => {
    await userEvent.click(screen.getByRole('button', {
      name: getTranslatedText('team.create-user-modal.tab-ai-agent'),
    }));
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  describe('Rendering', () => {
    it('does not render when isOpen=false', () => {
      render(<CreateUserModal isOpen={false} onClose={mockOnClose} />);

      expect(screen.queryByTestId('create-user-modal-header')).not.toBeInTheDocument();
    });

    it('renders when isOpen=true', () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByTestId('create-user-modal-header')).toBeInTheDocument();
    });

    it('displays all form fields', () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.last-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.email'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-user-modal.status'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.password'))).toBeInTheDocument();
    });

    it('displays submit button', () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.submit') })).toBeInTheDocument();
    });

    it('displays password copy button', () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.copy') })).toBeInTheDocument();
    });
  });

  describe('AI agent form', () => {
    it('renders AI agent fields from the modal tab', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      await openAIAgentTab();

      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.last-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.position'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-ai-agent-modal.model'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.endpoint'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.api-key'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-ai-agent-modal.system-prompt'))).toBeInTheDocument();
    });

    it('preserves both forms while switching tabs', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const userFirstName = screen.getByLabelText(
        getTranslatedText('team.create-user-modal.first-name'),
      );
      const generatedPassword = screen.getByLabelText(
        getTranslatedText('team.create-user-modal.password'),
      ).getAttribute('value');
      await userEvent.type(userFirstName, 'User draft');

      await openAIAgentTab();
      const agentFirstName = screen.getByLabelText(
        getTranslatedText('team.create-user-modal.first-name'),
      );
      await userEvent.type(agentFirstName, 'Agent draft');

      await userEvent.click(screen.getByText(getTranslatedText('team.create-user-modal.tab-user')));
      expect(screen.getByLabelText(
        getTranslatedText('team.create-user-modal.first-name'),
      )).toHaveValue('User draft');
      expect(screen.getByLabelText(
        getTranslatedText('team.create-user-modal.password'),
      )).toHaveValue(generatedPassword);

      await openAIAgentTab();
      expect(screen.getByDisplayValue('Agent draft')).toBeInTheDocument();
    });

    it('localizes the required model error', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      const submitButton = screen.getByRole('button', {
        name: getTranslatedText('team.create-ai-agent-modal.submit'),
      });
      fireEvent.submit(submitButton.closest('form')!);

      const modelDropdown = screen.getByText(
        getTranslatedText('team.create-ai-agent-modal.model'),
      ).closest('.react-select') as HTMLElement;
      expect(await within(modelDropdown).findByText(
        getTranslatedText('team.create-ai-agent-modal.validation-required'),
      )).toBeInTheDocument();
      expect(screen.queryByText('team.create-ai-agent-modal.validation-required')).not.toBeInTheDocument();
    });

    it('requires the endpoint protocol', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      const endpointInput = screen.getByLabelText(
        getTranslatedText('team.create-ai-agent-modal.endpoint'),
      );
      await userEvent.type(endpointInput, 'api.example.com');
      await userEvent.tab();

      expect(await screen.findByText(getTranslatedText('validation.url-invalid'))).toBeInTheDocument();
    });

    it('keeps the AI agent form visible during the close animation', async () => {
      const { rerender } = render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      rerender(<CreateUserModal isOpen={false} onClose={mockOnClose} />);

      expect(screen.getByLabelText(
        getTranslatedText('team.create-ai-agent-modal.endpoint'),
      )).toBeInTheDocument();
    });

    it('validates required fields with Formik and submits valid values', async () => {
      const onCreateAIAgent = jest.fn();
      render(
        <CreateUserModal
          isOpen={true}
          onClose={mockOnClose}
          onCreateAIAgent={onCreateAIAgent}
        />,
      );
      await openAIAgentTab();
      const submitButton = screen.getByRole('button', {
        name: getTranslatedText('team.create-ai-agent-modal.submit'),
      });
      expect(submitButton).toBeDisabled();

      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name')),
        'Ada',
      );
      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-user-modal.last-name')),
        'Agent',
      );
      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.position')),
        'Support specialist',
      );
      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.endpoint')),
        'https://api.example.com/v1',
      );
      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.api-key')),
        'secret-key',
      );
      const modelLabel = screen.getByText(getTranslatedText('team.create-ai-agent-modal.model'));
      const modelDropdown = modelLabel.closest('.react-select')!
        .querySelector('.react-select__control') as HTMLElement;
      await userEvent.click(modelDropdown);
      await userEvent.click(screen.getByText('OpenAI'));

      await waitFor(() => expect(submitButton).not.toBeDisabled());
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(onCreateAIAgent).toHaveBeenCalledWith(expect.objectContaining({
          firstName: 'Ada',
          lastName: 'Agent',
          position: 'Support specialist',
          model: 'openai',
          endpoint: 'https://api.example.com/v1',
          apiKey: 'secret-key',
        }));
      });
      expect(mockDispatch).not.toHaveBeenCalled();
    });
  });

  describe('Form validation', () => {
    it('submit button is disabled when form is empty (dirty=false)', () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      expect(firstNameInput.value).toBe('');
      expect(lastNameInput.value).toBe('');
      expect(emailInput.value).toBe('');
      expect(submitButton).toBeDisabled();
    });

    it('submit button is disabled when only one field is filled', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();

      await userEvent.clear(firstNameInput);
      await userEvent.type(firstNameInput, 'John');
      const submitButton = getSubmitButton();

      await waitFor(() => {
        expect(firstNameInput.value).toBe('John');
        expect(lastNameInput.value).toBe('');
        expect(emailInput.value).toBe('');
        expect(submitButton).toBeDisabled();
      });
    });

    it('submit button is disabled with invalid email (dirty=true, isValid=false)', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'invalid-email');
      fireEvent.blur(emailInput);

      await waitFor(() => {
        expect(emailInput.value).toBe('invalid-email');
        expect(submitButton).toBeDisabled();
      });
    });

    it('submit button is disabled with invalid password (dirty=true, isValid=false due to password)', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { passwordInput } = getFormFields();
      const submitButton = getSubmitButton();

      await userEvent.clear(passwordInput);
      await userEvent.type(passwordInput, '12345');
      fireEvent.blur(passwordInput);

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });

    it('submit button is enabled with valid form (dirty=true, isValid=true)', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      const submitButton = getSubmitButton();

      await userEvent.clear(firstNameInput);
      await userEvent.type(firstNameInput, 'John');
      await userEvent.clear(lastNameInput);
      await userEvent.type(lastNameInput, 'Doe');
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'john.doe@example.com');
      await userEvent.clear(passwordInput);
      await userEvent.type(passwordInput, 'valid-password-123');
      fireEvent.blur(passwordInput);

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
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { passwordInput } = getFormFields();
      const copyButton = getCopyButton();

      await userEvent.click(copyButton);

      expect(copyToClipboard).toHaveBeenCalledWith(passwordInput.value);
      expect(NotificationManager.success).toHaveBeenCalledWith({
        message: PASSWORD_COPIED_MESSAGE,
      });
    });

    it('copies changed password on button click', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { passwordInput } = getFormFields();
      const newPassword = 'my-custom-password-123';

      await userEvent.clear(passwordInput);
      await userEvent.type(passwordInput, newPassword);
      await waitFor(() => {
        expect(passwordInput.value).toBe(newPassword);
      });

      const copyButton = getCopyButton();
      await userEvent.click(copyButton);

      expect(copyToClipboard).toHaveBeenCalledWith(newPassword);
      expect(NotificationManager.success).toHaveBeenCalledWith({
        message: PASSWORD_COPIED_MESSAGE,
      });
    });
  });

  describe('Form submission', () => {
    it('calls createUser with correct data on submit', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      const submitButton = getSubmitButton();

      await userEvent.clear(firstNameInput);
      await userEvent.type(firstNameInput, 'John');
      await userEvent.clear(lastNameInput);
      await userEvent.type(lastNameInput, 'Doe');
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'john.doe@example.com');

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
      await userEvent.click(submitButton);

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
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();

      await userEvent.clear(firstNameInput);
      await userEvent.type(firstNameInput, 'Admin');
      await userEvent.clear(lastNameInput);
      await userEvent.type(lastNameInput, 'User');
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'admin@example.com');

      const roleDropdown = getRoleDropdown();
      await userEvent.click(roleDropdown);

      await waitFor(async () => {
        const adminOption = screen.getByText(ADMIN_OPTION_TEXT);
        await userEvent.click(adminOption);
      });

      const submitButton = getSubmitButton();
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });

      await userEvent.click(submitButton);

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
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      await userEvent.clear(firstNameInput);
      await userEvent.type(firstNameInput, 'John');
      await userEvent.clear(lastNameInput);
      await userEvent.type(lastNameInput, 'Doe');
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'john.doe@example.com');
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });

      await userEvent.click(submitButton);
      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Form reinitialization', () => {
    it('form resets and password is regenerated on reopen', async () => {
      const { unmount } = render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      await userEvent.clear(firstNameInput);
      await userEvent.type(firstNameInput, 'John');
      await userEvent.clear(lastNameInput);
      await userEvent.type(lastNameInput, 'Doe');
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'john.doe@example.com');

      const roleDropdown = getRoleDropdown();
      await userEvent.click(roleDropdown);
      await waitFor(async () => {
        const adminOption = screen.getByText(ADMIN_OPTION_TEXT);
        await userEvent.click(adminOption);
      });

      await waitFor(() => {
        const submitButton = getSubmitButton();
        expect(submitButton).not.toBeDisabled();
      });

      unmount();
      jest.clearAllMocks();

      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);

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
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      const closeButtons = screen.getAllByRole('button', { name: 'Close modal' });
      const headerCloseButton = closeButtons.find((button) => button.classList.contains('close-button'));
      expect(headerCloseButton).toBeInTheDocument();
      await userEvent.click(headerCloseButton!);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});

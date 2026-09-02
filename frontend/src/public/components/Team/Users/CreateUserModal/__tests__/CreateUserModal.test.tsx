import * as React from 'react';
import { act, render, screen, fireEvent, waitFor, within, cleanup } from '@testing-library/react';
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

  const fillInput = (input: HTMLInputElement, value: string) => {
    fireEvent.change(input, { target: { value } });
    fireEvent.blur(input);
  };

  const openModal = async () => {
    render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
    await screen.findByTestId('create-user-modal-header');
  };

  beforeEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  afterEach(() => {
    cleanup();
    document.body.style.overflow = '';
  });

  describe('Rendering', () => {
    it('does not render when isOpen=false', () => {
      render(<CreateUserModal isOpen={false} onClose={mockOnClose} />);

      expect(screen.queryByTestId('create-user-modal-header')).not.toBeInTheDocument();
    });

    it('renders when isOpen=true', async () => {
      await openModal();

      expect(screen.getByTestId('create-user-modal-header')).toBeInTheDocument();
    });

    it('displays all form fields', async () => {
      await openModal();

      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.last-name'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.email'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-user-modal.status'))).toBeInTheDocument();
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.password'))).toBeInTheDocument();
    });

    it('displays submit button', async () => {
      await openModal();

      expect(screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.submit') })).toBeInTheDocument();
    });

    it('displays password copy button', async () => {
      await openModal();

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

    it('clears the avatar input after upload so the same file can be selected again', async () => {
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      const avatarInput = screen.getByLabelText(
        getTranslatedText('team.create-ai-agent-modal.upload'),
      ) as HTMLInputElement;
      await userEvent.upload(avatarInput, new File(['avatar'], 'avatar.png', { type: 'image/png' }));

      expect(avatarInput.value).toBe('');
    });

    it('ignores an old file read after generating a newer avatar', async () => {
      const readers: FileReader[] = [];
      const readSpy = jest.spyOn(FileReader.prototype, 'readAsDataURL')
        .mockImplementation(function mockRead(this: FileReader) {
          readers.push(this);
        });
      render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      await userEvent.type(screen.getByLabelText(
        getTranslatedText('team.create-user-modal.first-name'),
      ), 'Ada');
      await userEvent.type(screen.getByLabelText(
        getTranslatedText('team.create-user-modal.last-name'),
      ), 'Agent');
      await userEvent.upload(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.upload')),
        new File(['old-avatar'], 'old.png', { type: 'image/png' }),
      );
      await userEvent.click(screen.getByRole('button', {
        name: getTranslatedText('team.create-ai-agent-modal.generate'),
      }));

      Object.defineProperty(readers[0], 'result', { value: 'data:image/png;base64,old' });
      act(() => readers[0].onload?.call(readers[0], new ProgressEvent('load')));
      readSpy.mockRestore();

      expect(screen.getByText('AA')).toBeInTheDocument();
      expect(document.querySelector('.modal__avatar-preview img')).not.toBeInTheDocument();
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

      const modelDropdown = screen.getByText(
        getTranslatedText('team.create-ai-agent-modal.model'),
      ).closest('.react-select') as HTMLElement;
      await userEvent.click(modelDropdown.querySelector('.react-select__control') as HTMLElement);
      await userEvent.tab();
      expect(await within(modelDropdown).findByText(
        getTranslatedText('team.create-ai-agent-modal.validation-required'),
      )).toBeInTheDocument();
      expect(within(modelDropdown).getAllByText('*')).toHaveLength(1);
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

    it('clears sensitive values and pending avatar reads on a quick reopen', async () => {
      const readers: FileReader[] = [];
      const readSpy = jest.spyOn(FileReader.prototype, 'readAsDataURL')
        .mockImplementation(function mockRead(this: FileReader) {
          readers.push(this);
        });
      const { rerender } = render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();
      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.api-key')),
        'secret-key',
      );
      await userEvent.upload(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.upload')),
        new File(['old-avatar'], 'old.png', { type: 'image/png' }),
      );

      rerender(<CreateUserModal isOpen={false} onClose={mockOnClose} />);
      rerender(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await waitFor(() => expect(screen.getByLabelText(
        getTranslatedText('team.create-user-modal.email'),
      )).toBeInTheDocument());
      Object.defineProperty(readers[0], 'result', { value: 'data:image/png;base64,old' });
      act(() => readers[0].onload?.call(readers[0], new ProgressEvent('load')));
      readSpy.mockRestore();
      await openAIAgentTab();

      expect(screen.getByLabelText(
        getTranslatedText('team.create-ai-agent-modal.api-key'),
      )).toHaveValue('');
      expect(document.querySelector('.modal__avatar-preview img')).not.toBeInTheDocument();
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
    it('submit button is disabled when form is empty (dirty=false)', async () => {
      await openModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      const submitButton = getSubmitButton();

      expect(firstNameInput.value).toBe('');
      expect(lastNameInput.value).toBe('');
      expect(emailInput.value).toBe('');
      expect(submitButton).toBeDisabled();
    });

    it('submit button is disabled when only one field is filled', async () => {
      await openModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      fillInput(firstNameInput, 'John');

      await waitFor(() => {
        expect(firstNameInput.value).toBe('John');
        expect(lastNameInput.value).toBe('');
        expect(emailInput.value).toBe('');
        expect(getSubmitButton()).toBeDisabled();
      });
    });

    it('submit button is disabled with invalid email (dirty=true, isValid=false)', async () => {
      await openModal();

      const { emailInput } = getFormFields();
      fillInput(emailInput, 'invalid-email');

      await waitFor(() => {
        expect(emailInput.value).toBe('invalid-email');
        expect(getSubmitButton()).toBeDisabled();
      });
    });

    it('submit button is disabled with invalid password (dirty=true, isValid=false due to password)', async () => {
      await openModal();

      const { passwordInput } = getFormFields();
      fillInput(passwordInput, '12345');

      await waitFor(() => {
        expect(getSubmitButton()).toBeDisabled();
      });
    });

    it('submit button is enabled with valid form (dirty=true, isValid=true)', async () => {
      await openModal();

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      fillInput(firstNameInput, 'John');
      fillInput(lastNameInput, 'Doe');
      fillInput(emailInput, 'john.doe@example.com');
      fillInput(passwordInput, 'valid-password-123');

      await waitFor(() => {
        expect(firstNameInput.value).toBe('John');
        expect(lastNameInput.value).toBe('Doe');
        expect(emailInput.value).toBe('john.doe@example.com');
        expect(passwordInput.value).toBe('valid-password-123');
        expect(getSubmitButton()).not.toBeDisabled();
      });
    });
  });

  describe('Password copying', () => {
    it('copies password to clipboard on button click', async () => {
      await openModal();

      const { passwordInput } = getFormFields();
      await userEvent.click(getCopyButton());

      expect(copyToClipboard).toHaveBeenCalledWith(passwordInput.value);
      expect(NotificationManager.success).toHaveBeenCalledWith({
        message: PASSWORD_COPIED_MESSAGE,
      });
    });

    it('copies changed password on button click', async () => {
      await openModal();

      const { passwordInput } = getFormFields();
      const newPassword = 'my-custom-password-123';
      fillInput(passwordInput, newPassword);

      await waitFor(() => {
        expect(passwordInput.value).toBe(newPassword);
      });

      await userEvent.click(getCopyButton());

      expect(copyToClipboard).toHaveBeenCalledWith(newPassword);
      expect(NotificationManager.success).toHaveBeenCalledWith({
        message: PASSWORD_COPIED_MESSAGE,
      });
    });
  });

  describe('Form submission', () => {
    it('calls createUser with correct data on submit', async () => {
      await openModal();

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      fillInput(firstNameInput, 'John');
      fillInput(lastNameInput, 'Doe');
      fillInput(emailInput, 'john.doe@example.com');

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });
      await userEvent.click(getSubmitButton());

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
      await openModal();

      const { firstNameInput, lastNameInput, emailInput, passwordInput } = getFormFields();
      fillInput(firstNameInput, 'Admin');
      fillInput(lastNameInput, 'User');
      fillInput(emailInput, 'admin@example.com');

      await userEvent.click(getRoleDropdown());
      await userEvent.click(await screen.findByText(ADMIN_OPTION_TEXT));

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });

      await userEvent.click(getSubmitButton());

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
      await openModal();

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      fillInput(firstNameInput, 'John');
      fillInput(lastNameInput, 'Doe');
      fillInput(emailInput, 'john.doe@example.com');

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });

      await userEvent.click(getSubmitButton());
      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Form reinitialization', () => {
    it('form resets and password is regenerated on reopen', async () => {
      const { unmount } = render(<CreateUserModal isOpen={true} onClose={mockOnClose} />);
      await screen.findByTestId('create-user-modal-header');

      const { firstNameInput, lastNameInput, emailInput } = getFormFields();
      fillInput(firstNameInput, 'John');
      fillInput(lastNameInput, 'Doe');
      fillInput(emailInput, 'john.doe@example.com');

      await userEvent.click(getRoleDropdown());
      await userEvent.click(await screen.findByText(ADMIN_OPTION_TEXT));

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });

      unmount();
      jest.clearAllMocks();

      await openModal();

      await waitFor(() => {
        expect(createPassword).toHaveBeenCalled();
      });

      await waitFor(() => {
        const {
          firstNameInput: newFirstNameInput,
          lastNameInput: newLastNameInput,
          emailInput: newEmailInput,
        } = getFormFields();
        expect(newFirstNameInput.value).toBe('');
        expect(newLastNameInput.value).toBe('');
        expect(newEmailInput.value).toBe('');
      });

      expect(getSubmitButton()).toBeDisabled();
      expect(getRoleDropdown()).toHaveTextContent(USER_OPTION_TEXT);
    });
  });

  describe('Modal closing', () => {
    it('calls onClose on close', async () => {
      await openModal();
      const closeButtons = screen.getAllByRole('button', { name: 'Close modal' });
      const headerCloseButton = closeButtons.find((button) => button.classList.contains('close-button'));
      expect(headerCloseButton).toBeInTheDocument();
      await userEvent.click(headerCloseButton!);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});

import * as React from 'react';
import { act, render, screen, fireEvent, waitFor, within, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { CreatePerformerModal } from '../CreatePerformerModal';
import { createUser } from '../../../../redux/accounts/slice';
import {
  cancelAIAgentAvatarUpload,
  createAIAgent,
  loadAIProviderModels,
  loadAIProviders,
  uploadAIAgentAvatar,
} from '../../../../redux/ai/slice';
import { NotificationManager } from '../../../UI/Notifications';
import { copyToClipboard } from '../../../../utils/helpers';
import { createPassword } from '../../../../utils/createPassword';
import { intlMock } from '../../../../__stubs__/intlMock';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
}));

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

const mockGenerateAgentAvatar = jest.fn();
jest.mock('../../AIAgents/utils/generateAgentAvatar', () => ({
  generateAgentAvatar: (initials: string) => mockGenerateAgentAvatar(initials),
}));

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../../../../redux/accounts/slice', () => ({
  createUser: jest.fn((payload) => ({ type: 'accounts/createUser', payload })),
}));

jest.mock('../../../UI/Notifications', () => ({
  NotificationManager: {
    success: jest.fn(),
    warning: jest.fn(),
  },
}));

jest.mock('../../../../utils/helpers', () => ({
  copyToClipboard: jest.fn(),
}));

jest.mock('../../../../utils/createPassword', () => ({
  createPassword: jest.fn(() => 'mock-password-123'),
}));

jest.mock('react-perfect-scrollbar', () => {
  const MockScrollbar = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  return {
    __esModule: true,
    default: MockScrollbar,
  };
});

describe('CreatePerformerModal', () => {
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

  const getSubmitButton = () =>
    screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.submit') });

  const getCopyButton = () => screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.copy') });

  const getRoleDropdown = () => {
    const label = screen.getByText(getTranslatedText('team.create-user-modal.status'));
    const dropdownContainer = label.closest('.react-select')!;
    return dropdownContainer.querySelector('.react-select__control') as HTMLElement;
  };

  const OPENROUTER_PROVIDER = {
    id: 1,
    name: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    apiKeyPrefix: 'sk-or-v1-01234',
    vendor: 'openrouter',
    isActive: true,
    usage: [],
  };

  const INTERNAL_PROVIDER = {
    id: 2,
    name: 'OpenAI compatible',
    baseUrl: 'https://llm.internal.example.com/v1',
    apiKeyPrefix: 'secret-key-abc',
    vendor: 'openai_compatible',
    isActive: true,
    usage: [],
  };

  const DEFAULT_MODELS = [
    { name: 'GPT-4o', slug: 'openai/gpt-4o' },
    { name: 'Claude Sonnet', slug: 'anthropic/claude-sonnet' },
  ];
  let createAgentState: { isLoading: boolean };
  let isAvatarUploading: boolean;

  const mockAIState = ({
    providers = [OPENROUTER_PROVIDER],
    models = { isLoading: false, providerId: 1, list: DEFAULT_MODELS },
    isLoadingProviders = false,
  }: { providers?: object[]; models?: object; isLoadingProviders?: boolean } = {}) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selector) =>
      selector({
        ai: {
          providers: { isLoading: isLoadingProviders, list: providers },
          createAgent: createAgentState,
          agentAvatarUpload: { isLoading: isAvatarUploading },
          agents: { isLoading: false, list: [] },
          models,
        },
      }),
    );
  };

  const openAIAgentTab = async () => {
    await userEvent.click(
      screen.getByRole('button', {
        name: getTranslatedText('team.create-user-modal.tab-ai-agent'),
      }),
    );
  };

  const fillInput = (input: HTMLInputElement, value: string) => {
    fireEvent.change(input, { target: { value } });
    fireEvent.blur(input);
  };

  const openModal = async () => {
    render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
    await screen.findByRole('button', { name: getTranslatedText('team.create-user-modal.tab-user') });
  };

  beforeEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
    createAgentState = { isLoading: false };
    isAvatarUploading = false;
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    mockAIState();
  });

  afterEach(() => {
    cleanup();
    document.body.style.overflow = '';
  });

  describe('Rendering', () => {
    it('does not render when isOpen=false', () => {
      render(<CreatePerformerModal isOpen={false} onClose={mockOnClose} />);

      expect(
        screen.queryByRole('button', { name: getTranslatedText('team.create-user-modal.tab-user') }),
      ).not.toBeInTheDocument();
    });

    it('renders when isOpen=true', async () => {
      await openModal();

      expect(
        screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.tab-user') }),
      ).toBeInTheDocument();
      expect(mockDispatch).toHaveBeenCalledWith(loadAIProviders());
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

      expect(
        screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.submit') }),
      ).toBeInTheDocument();
    });

    it('displays password copy button', async () => {
      await openModal();

      expect(
        screen.getByRole('button', { name: getTranslatedText('team.create-user-modal.copy') }),
      ).toBeInTheDocument();
    });
  });

  describe('AI agent form', () => {
    const getNameInput = () =>
      screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.name')) as HTMLInputElement;

    const getDropdownControl = (labelId: string) => {
      const label = screen.getByText(getTranslatedText(labelId));
      return label.closest('.react-select')!.querySelector('.react-select__control') as HTMLElement;
    };

    const getAgentSubmitButton = () =>
      screen.getByRole('button', { name: getTranslatedText('team.create-ai-agent-modal.submit') });

    const fillAgentForm = async () => {
      await userEvent.type(getNameInput(), 'Research assistant');
      await userEvent.click(getDropdownControl('team.create-ai-agent-modal.model'));
      await userEvent.click(screen.getByText('GPT-4o'));
      await userEvent.type(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.system-prompt')),
        'You are helpful.',
      );
      await waitFor(() => expect(getAgentSubmitButton()).toBeEnabled());
    };

    it('renders the agent fields once a provider exists', async () => {
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      expect(getNameInput()).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-ai-agent-modal.provider'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-ai-agent-modal.model'))).toBeInTheDocument();
      expect(screen.getByText(getTranslatedText('team.create-ai-agent-modal.system-prompt'))).toBeInTheDocument();
    });

    it('shows the register-a-provider hint instead of the form when there are no providers', async () => {
      mockAIState({ providers: [] });
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      expect(screen.getByTestId('ai-agent-no-providers-hint')).toBeInTheDocument();
      expect(screen.queryByLabelText(getTranslatedText('team.create-ai-agent-modal.name'))).not.toBeInTheDocument();
    });

    it('closes the modal and opens Integrations from the no-providers hint', async () => {
      mockAIState({ providers: [] });
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      await userEvent.click(
        screen.getByRole('button', { name: getTranslatedText('team.create-ai-agent-modal.go-to-integrations') }),
      );

      expect(mockOnClose).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(ERoutes.Integrations);
    });

    it('shows a loader instead of the no-providers hint while providers are loading', async () => {
      mockAIState({ providers: [], isLoadingProviders: true });
      const { baseElement } = render(<CreatePerformerModal isOpen onClose={mockOnClose} />);
      await openAIAgentTab();

      expect(baseElement.querySelector('.spinner')).toBeInTheDocument();
      expect(screen.queryByTestId('ai-agent-no-providers-hint')).not.toBeInTheDocument();
      expect(screen.queryByLabelText(getTranslatedText('team.create-ai-agent-modal.name'))).not.toBeInTheDocument();
    });

    it('preselects the provider and loads its models when the account has exactly one', async () => {
      mockAIState({ models: { isLoading: false, providerId: null, list: [] } });
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledWith(loadAIProviderModels(1));
      });
      expect(screen.getByText('OpenRouter — sk-or-v1-01234')).toBeInTheDocument();
    });

    const getAvatarUploadAction = () =>
      mockDispatch.mock.calls.map(([action]) => action).find(({ type }) => type === uploadAIAgentAvatar.type);

    const uploadAvatar = (name = 'avatar.png') =>
      userEvent.upload(
        screen.getByLabelText(getTranslatedText('team.create-ai-agent-modal.upload')),
        new File([name], name, { type: 'image/png' }),
      );

    it('dispatches the avatar upload and clears the input so the same file can be selected again', async () => {
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      const avatarInput = screen.getByLabelText(
        getTranslatedText('team.create-ai-agent-modal.upload'),
      ) as HTMLInputElement;
      await uploadAvatar();

      expect(avatarInput.value).toBe('');
      expect(getAvatarUploadAction().payload.file.name).toBe('avatar.png');

      await act(async () => {
        getAvatarUploadAction().payload.onSuccess('https://files.example.com/avatar.png');
      });
      expect(document.querySelector('.ai-agent-form__avatar-preview img')).toHaveAttribute(
        'src',
        'https://files.example.com/avatar.png',
      );
    });

    it('blocks agent creation while the avatar uploads and submits the uploaded url', async () => {
      const { rerender } = render(<CreatePerformerModal isOpen onClose={mockOnClose} />);
      await openAIAgentTab();
      await fillAgentForm();
      await uploadAvatar();

      isAvatarUploading = true;
      rerender(<CreatePerformerModal isOpen onClose={mockOnClose} />);
      expect(getAgentSubmitButton()).toBeDisabled();

      await act(async () => {
        getAvatarUploadAction().payload.onSuccess('https://files.example.com/avatar.png');
      });
      isAvatarUploading = false;
      rerender(<CreatePerformerModal isOpen onClose={mockOnClose} />);

      await waitFor(() => expect(getAgentSubmitButton()).toBeEnabled());
      await userEvent.click(getAgentSubmitButton());
      await waitFor(() =>
        expect(mockDispatch).toHaveBeenCalledWith(
          expect.objectContaining({
            type: createAIAgent.type,
            payload: expect.objectContaining({ photo: 'https://files.example.com/avatar.png' }),
          }),
        ),
      );
    });

    it('uploads a generated avatar on Generate', async () => {
      mockGenerateAgentAvatar.mockResolvedValue(new File(['png'], 'ai-agent-avatar.png', { type: 'image/png' }));
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();
      await userEvent.type(getNameInput(), 'Ada Agent');

      await userEvent.click(
        screen.getByRole('button', { name: getTranslatedText('team.create-ai-agent-modal.generate') }),
      );

      await waitFor(() => expect(getAvatarUploadAction()).toBeDefined());
      expect(mockGenerateAgentAvatar).toHaveBeenCalledWith('AA');
      expect(getAvatarUploadAction().payload.file.name).toBe('ai-agent-avatar.png');
      await act(async () => {
        getAvatarUploadAction().payload.onSuccess('https://files.example.com/generated.png');
      });
      expect(document.querySelector('.ai-agent-form__avatar-preview img')).toHaveAttribute(
        'src',
        'https://files.example.com/generated.png',
      );
    });

    it('preserves both forms while switching tabs', async () => {
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);

      const userFirstName = screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name'));
      const generatedPassword = screen
        .getByLabelText(getTranslatedText('team.create-user-modal.password'))
        .getAttribute('value');
      await userEvent.type(userFirstName, 'User draft');

      await openAIAgentTab();
      await userEvent.type(getNameInput(), 'Agent draft');

      await userEvent.click(screen.getByText(getTranslatedText('team.create-user-modal.tab-user')));
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.first-name'))).toHaveValue('User draft');
      expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.password'))).toHaveValue(
        generatedPassword,
      );

      await openAIAgentTab();
      expect(screen.getByDisplayValue('Agent draft')).toBeInTheDocument();
    });

    it('localizes the required model error', async () => {
      render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      const modelDropdown = screen
        .getByText(getTranslatedText('team.create-ai-agent-modal.model'))
        .closest('.react-select') as HTMLElement;
      await userEvent.click(modelDropdown.querySelector('.react-select__control') as HTMLElement);
      await userEvent.tab();
      expect(
        await within(modelDropdown).findByText(getTranslatedText('validation.field-required')),
      ).toBeInTheDocument();
      expect(within(modelDropdown).getAllByText('*')).toHaveLength(1);
      expect(screen.queryByText('validation.field-required')).not.toBeInTheDocument();
    });

    it('keeps the AI agent form visible during the close animation', async () => {
      const { rerender } = render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      rerender(<CreatePerformerModal isOpen={false} onClose={mockOnClose} />);

      expect(getNameInput()).toBeInTheDocument();
    });

    it('clears the draft and cancels a pending avatar upload on a quick reopen', async () => {
      const { rerender } = render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();
      await userEvent.type(getNameInput(), 'Draft agent');
      await uploadAvatar('old.png');
      mockDispatch.mockClear();

      rerender(<CreatePerformerModal isOpen={false} onClose={mockOnClose} />);
      rerender(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await waitFor(() =>
        expect(screen.getByLabelText(getTranslatedText('team.create-user-modal.email'))).toBeInTheDocument(),
      );
      await openAIAgentTab();

      expect(mockDispatch).toHaveBeenCalledWith(cancelAIAgentAvatarUpload());
      expect(getNameInput()).toHaveValue('');
      expect(document.querySelector('.ai-agent-form__avatar-preview img')).not.toBeInTheDocument();
    });

    it('cancels a pending avatar upload when the agent form unmounts', async () => {
      const { unmount } = render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();
      await uploadAvatar();
      mockDispatch.mockClear();

      unmount();

      expect(mockDispatch).toHaveBeenCalledWith(cancelAIAgentAvatarUpload());
    });

    it('clears the picked model and reloads the list when the provider changes', async () => {
      mockAIState({
        providers: [OPENROUTER_PROVIDER, INTERNAL_PROVIDER],
        models: { isLoading: false, providerId: null, list: [] },
      });
      const { rerender } = render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      await userEvent.click(getDropdownControl('team.create-ai-agent-modal.provider'));
      await userEvent.click(screen.getByText('OpenRouter — sk-or-v1-01234'));
      await waitFor(() => expect(mockDispatch).toHaveBeenCalledWith(loadAIProviderModels(1)));

      mockAIState({
        providers: [OPENROUTER_PROVIDER, INTERNAL_PROVIDER],
        models: { isLoading: false, providerId: 1, list: DEFAULT_MODELS },
      });
      rerender(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await userEvent.click(getDropdownControl('team.create-ai-agent-modal.model'));
      await userEvent.click(screen.getByText('GPT-4o'));
      expect(screen.getByText('GPT-4o')).toBeInTheDocument();

      await userEvent.click(getDropdownControl('team.create-ai-agent-modal.provider'));
      await userEvent.click(screen.getByText('OpenAI compatible — secret-key-abc'));

      await waitFor(() => expect(mockDispatch).toHaveBeenCalledWith(loadAIProviderModels(2)));
      expect(screen.queryByText('GPT-4o')).not.toBeInTheDocument();
    });

    it('dispatches agent creation and leaves closing to the saga', async () => {
      const { rerender } = render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await openAIAgentTab();

      const submitButton = getAgentSubmitButton();
      // The sole provider is auto-preselected; wait for validation to settle instead of asserting a race.
      await waitFor(() => expect(getAgentSubmitButton()).toBeDisabled());

      await fillAgentForm();
      await userEvent.click(submitButton);

      await waitFor(() =>
        expect(mockDispatch).toHaveBeenCalledWith(expect.objectContaining({ type: createAIAgent.type })),
      );
      const action = mockDispatch.mock.calls
        .map(([dispatched]) => dispatched)
        .find(({ type }) => type === createAIAgent.type);
      expect(action).toMatchObject({
        payload: {
          name: 'Research assistant',
          providerId: 1,
          model: 'openai/gpt-4o',
          systemPrompt: 'You are helpful.',
          photo: null,
          isActive: true,
        },
      });
      expect(mockOnClose).not.toHaveBeenCalled();

      createAgentState = { isLoading: true };
      rerender(<CreatePerformerModal isOpen onClose={mockOnClose} />);
      expect(getAgentSubmitButton()).toBeDisabled();
    });

    it('keeps the agent draft after an API failure and permits retry', async () => {
      const { rerender } = render(<CreatePerformerModal isOpen onClose={mockOnClose} />);
      await openAIAgentTab();
      await fillAgentForm();
      await userEvent.click(getAgentSubmitButton());

      await waitFor(() =>
        expect(mockDispatch).toHaveBeenCalledWith(expect.objectContaining({ type: createAIAgent.type })),
      );
      createAgentState = { isLoading: true };
      rerender(<CreatePerformerModal isOpen onClose={mockOnClose} />);
      createAgentState = { isLoading: false };
      rerender(<CreatePerformerModal isOpen onClose={mockOnClose} />);

      expect(mockOnClose).not.toHaveBeenCalled();
      expect(getNameInput()).toHaveValue('Research assistant');
      expect(getAgentSubmitButton()).toBeEnabled();
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
        expect(createUser).toHaveBeenCalledTimes(1);
      });
      expect(mockDispatch.mock.calls.filter(([action]) => action.type === 'accounts/createUser')).toHaveLength(1);
    });
  });

  describe('Form reinitialization', () => {
    it('form resets and password is regenerated on reopen', async () => {
      const { unmount } = render(<CreatePerformerModal isOpen={true} onClose={mockOnClose} />);
      await screen.findByRole('button', { name: getTranslatedText('team.create-user-modal.tab-user') });

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

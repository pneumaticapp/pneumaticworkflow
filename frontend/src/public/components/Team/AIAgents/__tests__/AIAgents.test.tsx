import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { AIAgents } from '../AIAgents';
import { deleteAIAgent, loadAIAgents, loadAIProviders, updateAIAgent } from '../../../../redux/ai/slice';
import { EAIVendor, IAIAgent, IAIProvider } from '../../../../types/ai';

jest.mock('../../../UI', () => ({
  Tooltip: ({ children, content }: any) => <div data-testid="tooltip" data-content={content}>{children}</div>,
}));

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, disabled }: any) => (
    <button onClick={onClick} data-testid={testId} disabled={disabled}>{label}</button>
  ),
}));

jest.mock('../../../UI/Buttons/AddButton', () => ({
  AddButton: ({ title, onClick, disabled }: any) => (
    <button data-testid="create-ai-agent-btn" onClick={onClick} disabled={disabled}>{title}</button>
  ),
}));

jest.mock('../../../UI/Typeography/Header', () => ({
  Header: ({ children }: any) => <p>{children}</p>,
}));

jest.mock('../../../UI/Modal/Modal', () => ({
  Modal: ({ children, isOpen }: any) => (isOpen ? <div role="dialog">{children}</div> : null),
}));

jest.mock('rc-switch', () => ({ checked, onChange, disabled }: any) => (
  <input
    type="checkbox"
    data-testid="active-switch"
    checked={checked}
    disabled={disabled}
    onChange={(e) => onChange(e.target.checked)}
  />
));

jest.mock('../../../PageTitle/PageTitle', () => ({
  PageTitle: () => <div />,
}));

jest.mock('../../TeamUserSkeleton', () => ({
  TeamUserSkeleton: () => <div data-testid="agent-skeleton" />,
}));

jest.mock('../../Users/CreateUserModal', () => ({
  CreateUserModal: ({ isOpen, initialTab }: any) =>
    isOpen ? <div data-testid="create-user-modal" data-initial-tab={initialTab} /> : null,
}));

jest.mock('../EditAIAgentModal', () => ({
  EditAIAgentModal: ({ agent }: any) =>
    agent ? <div data-testid="edit-ai-agent-modal" data-agent-id={agent.id} /> : null,
}));

const buildProvider = (overrides: Partial<IAIProvider> = {}): IAIProvider => ({
  id: 1,
  name: 'OpenRouter',
  baseUrl: 'https://openrouter.ai/api/v1',
  apiKeyPrefix: 'sk-or',
  vendor: EAIVendor.OpenRouter,
  isActive: true,
  usage: [],
  ...overrides,
});

const buildAgent = (overrides: Partial<IAIAgent> = {}): IAIAgent => ({
  id: 10,
  name: 'Research assistant',
  photo: null,
  isActive: true,
  providerId: 1,
  model: 'openai/gpt-4o',
  systemPrompt: 'You are helpful.',
  ...overrides,
});

describe('AIAgents', () => {
  const mockDispatch = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  const mockState = ({
    agents = [] as IAIAgent[],
    providers = [buildProvider()],
    agentsLoaded = true,
    providersLoaded = true,
  } = {}) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selector) =>
      selector({
        ai: {
          providers: { isLoading: false, isLoaded: providersLoaded, list: providers },
          agents: { isLoading: !agentsLoaded, isLoaded: agentsLoaded, list: agents },
          models: { isLoading: false, providerId: null, list: [] },
          isSaving: false,
        },
      }),
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    mockState();
  });

  it('loads agents and providers on mount', () => {
    render(<AIAgents />);

    expect(mockDispatch).toHaveBeenCalledWith(loadAIAgents());
    expect(mockDispatch).toHaveBeenCalledWith(loadAIProviders());
  });

  it('disables the create button and explains why while there are no providers', () => {
    mockState({ providers: [] });

    render(<AIAgents />);

    expect(screen.getByTestId('create-ai-agent-btn')).toBeDisabled();
    expect(screen.getByTestId('tooltip')).toHaveAttribute(
      'data-content',
      t('team.create-ai-agent-modal.no-providers-hint'),
    );
  });

  it('opens the creation modal on the AI agent tab when a provider exists', () => {
    render(<AIAgents />);

    const createButton = screen.getByTestId('create-ai-agent-btn');
    expect(createButton).toBeEnabled();

    userEvent.click(createButton);

    expect(screen.getByTestId('create-user-modal')).toHaveAttribute('data-initial-tab', 'ai-agent');
  });

  it('renders the agent with its provider name, model and inactive badge', () => {
    mockState({ agents: [buildAgent({ isActive: false })] });

    render(<AIAgents />);

    expect(screen.getByText('Research assistant')).toBeInTheDocument();
    expect(screen.getByText(/OpenRouter/)).toBeInTheDocument();
    expect(screen.getByText(/openai\/gpt-4o/)).toBeInTheDocument();
    expect(screen.getByTestId('ai-agent-inactive-10')).toBeInTheDocument();
  });

  it('toggles is_active from the card', () => {
    mockState({ agents: [buildAgent({ isActive: true })] });

    render(<AIAgents />);

    userEvent.click(screen.getByTestId('active-switch'));

    expect(mockDispatch).toHaveBeenCalledWith(updateAIAgent({ id: 10, isActive: false }));
  });

  it('opens the edit modal for the picked agent', () => {
    mockState({ agents: [buildAgent()] });

    render(<AIAgents />);

    userEvent.click(screen.getByTestId('edit-ai-agent-10'));

    expect(screen.getByTestId('edit-ai-agent-modal')).toHaveAttribute('data-agent-id', '10');
  });

  it('deletes the agent through the confirmation modal', () => {
    mockState({ agents: [buildAgent()] });

    render(<AIAgents />);

    userEvent.click(screen.getByTestId('delete-ai-agent-10'));
    userEvent.click(screen.getByTestId('confirm-delete-ai-agent'));

    expect(mockDispatch).toHaveBeenCalledWith(deleteAIAgent(10));
  });

  it('shows the empty state when no agents exist', () => {
    render(<AIAgents />);

    expect(screen.getByTestId('empty-ai-agents-message')).toBeInTheDocument();
  });
});

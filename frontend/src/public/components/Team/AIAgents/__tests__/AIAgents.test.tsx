import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { AIAgents } from '../AIAgents';
import { deleteAIAgent, loadAIAgents, loadAIProviders, updateAIAgent } from '../../../../redux/ai/slice';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';
import { EAIVendor, IAIAgent, IAIProvider } from '../../../../types/ai';

jest.mock('../../../UI', () => ({
  Dropdown: ({ renderToggle, options, toggleProps }: any) => {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
      <div>
        <button type="button" data-testid={toggleProps?.['data-testid']} onClick={() => setIsOpen(!isOpen)}>
          {renderToggle(isOpen)}
        </button>
        {isOpen &&
          options.map(({ label, onClick }: any) => (
            <button key={label} type="button" onClick={() => onClick(() => {})}>
              {label}
            </button>
          ))}
      </div>
    );
  },
}));

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, disabled }: any) => (
    <button onClick={onClick} data-testid={testId} disabled={disabled}>
      {label}
    </button>
  ),
}));

jest.mock('../../../UI/Buttons/AddButton', () => ({
  AddButton: ({ title, onClick, disabled }: any) => (
    <button data-testid="create-ai-agent-btn" onClick={onClick} disabled={disabled}>
      {title}
    </button>
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

jest.mock('../../Users/CreatePerformerModal', () => ({
  CreatePerformerModal: ({ isOpen, initialTab }: any) =>
    isOpen ? <div data-testid="create-user-modal" data-initial-tab={initialTab} /> : null,
}));

jest.mock('../EditAIAgentModal', () => ({
  EditAIAgentModal: ({ agent }: any) =>
    agent ? <div data-testid="edit-ai-agent-modal" data-agent-id={agent.id} /> : null,
}));

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
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
          providers: { isLoading: !providersLoaded, list: providers },
          agents: { isLoading: !agentsLoaded, list: agents },
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

  it('hides the create button and links to Integrations while there are no providers', () => {
    mockState({ providers: [] });

    render(<AIAgents />);

    expect(screen.queryByTestId('create-ai-agent-btn')).not.toBeInTheDocument();

    const hint = screen.getByTestId('no-ai-providers-hint');
    expect(hint).toHaveTextContent(t('team.create-ai-agent-modal.no-providers-hint'));

    userEvent.click(screen.getByTestId('go-to-ai-providers'));

    expect(history.push).toHaveBeenCalledWith(ERoutes.Integrations);
  });

  it('renders the create button while providers are loading', () => {
    mockState({ providers: [], providersLoaded: false });

    render(<AIAgents />);

    expect(screen.getByTestId('create-ai-agent-btn')).toBeEnabled();
    expect(screen.queryByTestId('no-ai-providers-hint')).not.toBeInTheDocument();
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

  it('opens the edit modal from the card dropdown', () => {
    mockState({ agents: [buildAgent()] });

    render(<AIAgents />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.edit')));

    expect(screen.getByTestId('edit-ai-agent-modal')).toHaveAttribute('data-agent-id', '10');
  });

  it('deletes the agent through the confirmation modal', () => {
    mockState({ agents: [buildAgent()] });

    render(<AIAgents />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.delete')));
    userEvent.click(screen.getByTestId('confirm-delete-ai-agent'));

    expect(mockDispatch).toHaveBeenCalledWith(deleteAIAgent(10));
  });

  it('shows the empty state when no agents exist', () => {
    render(<AIAgents />);

    expect(screen.getByTestId('empty-ai-agents-message')).toBeInTheDocument();
  });
});

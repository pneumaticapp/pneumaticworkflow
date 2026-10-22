import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { AIAgents } from '../AIAgents';
import { CreatePerformerModal } from '../../Users/CreatePerformerModal';
import { ECreatePerformerModalTab } from '../../Users/CreatePerformerModal/types';
import { EAIVendor } from '../../../../api/ai/types';
import type { IAIAgent, IAIProvider } from '../../../../api/ai/types';
import { loadAIAgents, loadAIProviders } from '../../../../redux/ai/slice';
import { closeCreateUserModal, openCreateUserModal } from '../../../../redux/accounts/slice';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/team/ai-agents/' } },
}));

jest.mock('../../Users/CreatePerformerModal', () => ({
  CreatePerformerModal: jest.fn(() => null),
}));

jest.mock('../../Users/TeamAgent', () => ({
  TeamAgent: ({ agent, providerName }: { agent: IAIAgent; providerName?: string }) => (
    <div data-testid="team-agent-card">{`${agent.name} · ${providerName}`}</div>
  ),
}));

jest.mock('../../../PageTitle', () => ({
  PageTitle: () => null,
}));

const getText = (id: string) => intlMock.formatMessage({ id });

const buildProvider = (overrides: Partial<IAIProvider> = {}): IAIProvider => ({
  id: 1,
  name: 'OpenRouter',
  baseUrl: 'https://openrouter.ai/api/v1',
  apiKeyPrefix: 'sk-or',
  vendor: EAIVendor.OpenRouter,
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

  const mockState = ({
    agents = [buildAgent()],
    providers = [buildProvider()],
    areAgentsLoading = false,
    areProvidersLoading = false,
  }: {
    agents?: IAIAgent[];
    providers?: IAIProvider[];
    areAgentsLoading?: boolean;
    areProvidersLoading?: boolean;
  } = {}) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selector) =>
      selector({
        accounts: { isCreateUserModalOpen: false },
        ai: {
          agents: { isLoading: areAgentsLoading, list: agents },
          providers: { isLoading: areProvidersLoading, list: providers },
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

  it('closes the shared create modal when leaving the tab', () => {
    const { unmount } = render(<AIAgents />);
    expect(mockDispatch).not.toHaveBeenCalledWith(closeCreateUserModal());

    unmount();

    expect(mockDispatch).toHaveBeenCalledWith(closeCreateUserModal());
  });

  it('lists agents sorted by name with their provider names', () => {
    mockState({ agents: [buildAgent({ id: 1, name: 'Zed' }), buildAgent({ id: 2, name: 'Ada' })] });

    render(<AIAgents />);

    expect(screen.getAllByTestId('team-agent-card').map((card) => card.textContent)).toEqual([
      'Ada · OpenRouter',
      'Zed · OpenRouter',
    ]);
  });

  it('opens the create modal on the AI agent tab', () => {
    render(<AIAgents />);

    userEvent.click(screen.getByRole('button', { name: new RegExp(getText('team.ai-agents.create-button')) }));

    expect(mockDispatch).toHaveBeenCalledWith(openCreateUserModal());
    expect(CreatePerformerModal).toHaveBeenCalledWith(
      expect.objectContaining({ initialTab: ECreatePerformerModalTab.AIAgent }),
      {},
    );
  });

  it('disables creation and points to Integrations when there are no providers', () => {
    mockState({ providers: [] });

    render(<AIAgents />);

    expect(screen.getByRole('button', { name: new RegExp(getText('team.ai-agents.create-button')) })).toBeDisabled();
    expect(screen.getByTestId('no-ai-providers-hint')).toHaveTextContent(
      getText('team.create-ai-agent-modal.no-providers-hint'),
    );
    userEvent.click(screen.getByRole('button', { name: getText('team.create-ai-agent-modal.go-to-integrations') }));
    expect(history.push).toHaveBeenCalledWith(ERoutes.Integrations);
  });

  it('does not show the providers hint while providers are loading', () => {
    mockState({ providers: [], areProvidersLoading: true });

    render(<AIAgents />);

    expect(screen.queryByTestId('no-ai-providers-hint')).not.toBeInTheDocument();
  });

  it('shows an empty state when there are no agents', () => {
    mockState({ agents: [] });

    render(<AIAgents />);

    expect(screen.getByTestId('empty-ai-agents-message')).toHaveTextContent(getText('team.ai-agents.empty'));
  });
});

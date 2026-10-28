import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { AIAgents } from '../AIAgents';
import { CreatePerformerModal } from '../../CreatePerformerModal';
import { ECreatePerformerModalTab } from '../../CreatePerformerModal/types';
import { EAIVendor } from '../../../../api/ai/types';
import type { IAIAgent, IAIProvider } from '../../../../api/ai/types';
import { loadAIAgents, loadAIProviders } from '../../../../redux/ai/slice';
import { openCreatePerformerModal } from '../../../../redux/team/slice';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/team/ai-agents/' } },
  checkSomeRouteIsActive: jest.fn(() => false),
}));

jest.mock('../../CreatePerformerModal', () => ({
  CreatePerformerModal: jest.fn(() => null),
}));

jest.mock('../TeamAgent', () => ({
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
    isAgentsLoading = false,
    isProvidersLoading = false,
  }: {
    agents?: IAIAgent[];
    providers?: IAIProvider[];
    isAgentsLoading?: boolean;
    isProvidersLoading?: boolean;
  } = {}) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selector) =>
      selector({
        ai: {
          agents: { isLoading: isAgentsLoading, list: agents },
          providers: { isLoading: isProvidersLoading, list: providers },
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

    expect(mockDispatch).toHaveBeenCalledWith(openCreatePerformerModal());
    expect(CreatePerformerModal).toHaveBeenCalledWith(
      expect.objectContaining({ initialTab: ECreatePerformerModalTab.AIAgent }),
      {},
    );
  });

  it('disables creation and points to Integrations below the empty state when there are no providers', () => {
    mockState({ agents: [], providers: [] });

    render(<AIAgents />);

    expect(screen.getByRole('button', { name: new RegExp(getText('team.ai-agents.create-button')) })).toBeDisabled();
    expect(screen.getByText(getText('team.ai-agents.empty'))).toBeInTheDocument();
    expect(screen.getByText(getText('team.create-ai-agent-modal.no-providers-hint'))).toBeInTheDocument();
    userEvent.click(screen.getByRole('button', { name: getText('team.create-ai-agent-modal.go-to-integrations') }));
    expect(history.push).toHaveBeenCalledWith(ERoutes.Integrations);
  });

  it('does not show the providers hint while providers are loading', () => {
    mockState({ agents: [], providers: [], isProvidersLoading: true });

    render(<AIAgents />);

    expect(screen.queryByText(getText('team.create-ai-agent-modal.no-providers-hint'))).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: getText('team.create-ai-agent-modal.go-to-integrations') }),
    ).not.toBeInTheDocument();
  });

  it('shows an empty state when there are no agents', () => {
    mockState({ agents: [] });

    render(<AIAgents />);

    expect(screen.getByText(getText('team.ai-agents.empty'))).toBeInTheDocument();
    expect(screen.queryByText(getText('team.create-ai-agent-modal.no-providers-hint'))).not.toBeInTheDocument();
  });
});

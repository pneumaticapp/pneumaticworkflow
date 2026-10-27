import * as React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { TeamAgent } from '../TeamAgent';
import { deleteAIAgent, updateAIAgent } from '../../../../redux/ai/slice';
import type { IAIAgent } from '../../../../api/ai/types';

interface IDropdownMockProps {
  renderToggle(isOpen: boolean): React.ReactNode;
  options: { label: string; onClick(): void }[];
  toggleProps?: { 'data-testid'?: string };
}

interface ISwitchMockProps {
  checked: boolean;
  onChange(checked: boolean): void;
  'data-testid'?: string;
}

jest.mock('../../../UI', () => ({
  ...jest.requireActual('../../../UI'),
  Dropdown: ({ renderToggle, options, toggleProps }: IDropdownMockProps) => {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
      <div>
        <button type="button" data-testid={toggleProps?.['data-testid']} onClick={() => setIsOpen(!isOpen)}>
          {renderToggle(isOpen)}
        </button>
        {isOpen &&
          options.map(({ label, onClick }) => (
            <button key={label} type="button" onClick={() => onClick()}>
              {label}
            </button>
          ))}
      </div>
    );
  },
}));

jest.mock('rc-switch', () => ({ checked, onChange, 'data-testid': testId }: ISwitchMockProps) => (
  <input type="checkbox" data-testid={testId} checked={checked} onChange={(e) => onChange(e.target.checked)} />
));

jest.mock('../EditAIAgentModal', () => ({
  EditAIAgentModal: ({ agent }: { agent: IAIAgent }) => (
    <div data-testid="edit-ai-agent-modal" data-agent-id={agent.id} />
  ),
}));

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

describe('TeamAgent', () => {
  const mockDispatch = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
  });

  it('renders the agent with its provider name, model and inactive badge', () => {
    render(<TeamAgent agent={buildAgent({ isActive: false })} providerName="OpenRouter" />);

    expect(screen.getByRole('article')).toHaveAttribute('data-testid', 'ai-agent-10');
    expect(screen.getByRole('heading', { level: 3, name: 'Research assistant' })).toBeInTheDocument();
    expect(screen.getByText(/OpenRouter/)).toBeInTheDocument();
    expect(screen.getByText(/openai\/gpt-4o/)).toBeInTheDocument();
    expect(screen.getByTestId('ai-agent-inactive-10')).toBeInTheDocument();
  });

  it('falls back to the unknown provider label', () => {
    render(<TeamAgent agent={buildAgent()} />);

    expect(screen.getByText(new RegExp(t('team.ai-agents.unknown-provider')))).toBeInTheDocument();
  });

  it('toggles isActive from the card', () => {
    render(<TeamAgent agent={buildAgent({ isActive: true })} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-toggle-10'));

    expect(mockDispatch).toHaveBeenCalledWith(updateAIAgent({ id: 10, isActive: false }));
  });

  it('opens the edit modal from the card dropdown', () => {
    render(<TeamAgent agent={buildAgent()} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.edit')));

    expect(screen.getByTestId('edit-ai-agent-modal')).toHaveAttribute('data-agent-id', '10');
  });

  it('deletes the agent through the confirmation modal', async () => {
    render(<TeamAgent agent={buildAgent()} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.delete')));
    const popup = screen
      .getByRole('heading', { level: 2, name: t('team.ai-agents.delete-modal-title') })
      .closest('.modal-content') as HTMLElement;
    expect(popup).toHaveTextContent(t('team.ai-agents.delete-confirm').replace('{name}', 'Research assistant'));
    userEvent.click(within(popup).getByRole('button', { name: t('team.ai-agents.delete') }));

    expect(mockDispatch).toHaveBeenCalledWith(deleteAIAgent(10));
    await waitFor(() => expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument());
  });

  it('closes the delete modal on cancel without dispatching', async () => {
    render(<TeamAgent agent={buildAgent()} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.delete')));
    userEvent.click(screen.getByRole('button', { name: t('integrations.cancel') }));

    await waitFor(() => expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument());
    expect(mockDispatch).not.toHaveBeenCalledWith(deleteAIAgent(10));
  });
});

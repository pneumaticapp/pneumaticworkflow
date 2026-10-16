import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { TeamAgent } from '../TeamAgent';
import { deleteAIAgent, updateAIAgent } from '../../../../redux/ai/slice';
import type { IAIAgent } from '../../../../types/ai';

interface IDropdownMockProps {
  renderToggle(isOpen: boolean): React.ReactNode;
  options: { label: string; onClick(): void }[];
  toggleProps?: { 'data-testid'?: string };
}

interface IButtonMockProps {
  label: string;
  onClick(): void;
  disabled?: boolean;
  'data-testid'?: string;
}

interface ISwitchMockProps {
  checked: boolean;
  onChange(checked: boolean): void;
  disabled?: boolean;
}

jest.mock('../../../UI', () => ({
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

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, disabled }: IButtonMockProps) => (
    <button onClick={onClick} data-testid={testId} disabled={disabled}>
      {label}
    </button>
  ),
}));

jest.mock('../../../UI/Typeography/Header', () => ({
  Header: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
}));

jest.mock('../../../UI/Modal/Modal', () => ({
  Modal: ({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) =>
    isOpen ? <div role="dialog">{children}</div> : null,
}));

jest.mock('rc-switch', () => ({ checked, onChange, disabled }: ISwitchMockProps) => (
  <input
    type="checkbox"
    data-testid="active-switch"
    checked={checked}
    disabled={disabled}
    onChange={(e) => onChange(e.target.checked)}
  />
));

jest.mock('../EditAIAgentModal', () => ({
  EditAIAgentModal: ({ agent }: { agent: IAIAgent | null }) =>
    agent ? <div data-testid="edit-ai-agent-modal" data-agent-id={agent.id} /> : null,
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
    (useSelector as unknown as jest.Mock).mockImplementation((selector) =>
      selector({
        ai: { isSaving: false },
      }),
    );
  });

  it('renders the agent with its provider name, model and inactive badge', () => {
    render(<TeamAgent agent={buildAgent({ isActive: false })} providerName="OpenRouter" />);

    expect(screen.getByText('Research assistant')).toBeInTheDocument();
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

    userEvent.click(screen.getByTestId('active-switch'));

    expect(mockDispatch).toHaveBeenCalledWith(updateAIAgent({ id: 10, isActive: false }));
  });

  it('opens the edit modal from the card dropdown', () => {
    render(<TeamAgent agent={buildAgent()} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.edit')));

    expect(screen.getByTestId('edit-ai-agent-modal')).toHaveAttribute('data-agent-id', '10');
  });

  it('deletes the agent through the confirmation modal', () => {
    render(<TeamAgent agent={buildAgent()} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.delete')));
    userEvent.click(screen.getByTestId('confirm-delete-ai-agent'));

    expect(mockDispatch).toHaveBeenCalledWith(deleteAIAgent(10));
  });

  it('closes the delete modal on cancel without dispatching', () => {
    render(<TeamAgent agent={buildAgent()} providerName="OpenRouter" />);

    userEvent.click(screen.getByTestId('ai-agent-more-10'));
    userEvent.click(screen.getByText(t('team.ai-agents.delete')));
    userEvent.click(screen.getByTestId('cancel-delete-ai-agent'));

    expect(screen.queryByTestId('delete-ai-agent-modal')).not.toBeInTheDocument();
    expect(mockDispatch).not.toHaveBeenCalledWith(deleteAIAgent(10));
  });
});

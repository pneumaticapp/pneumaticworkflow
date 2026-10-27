import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { EditAIAgentModal } from '../EditAIAgentModal';
import { updateAIAgent } from '../../../../redux/ai/slice';
import type { IAIAgent } from '../../../../api/ai/types';
import type { IAIAgentFormValues } from '../../Users/CreatePerformerModal/types';

jest.mock('../../../UI/BaseModal', () => ({
  BaseModal: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ModalHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('../../Users/CreatePerformerModal/CreateAIAgentForm', () => ({
  CreateAIAgentForm: ({
    initialValues,
    onSubmit,
  }: {
    initialValues: IAIAgentFormValues;
    onSubmit(values: IAIAgentFormValues): void;
  }) => (
    <button
      type="button"
      data-testid="submit-edit-agent-form"
      data-initial-values={JSON.stringify(initialValues)}
      onClick={() => onSubmit(initialValues)}
    />
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

describe('EditAIAgentModal', () => {
  const mockDispatch = jest.fn();
  const onClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
  });

  it('maps the agent to form initial values', () => {
    render(<EditAIAgentModal agent={buildAgent()} onClose={onClose} />);

    const form = screen.getByTestId('submit-edit-agent-form');
    expect(JSON.parse(form.getAttribute('data-initial-values') as string)).toEqual({
      name: 'Research assistant',
      providerId: '1',
      model: 'openai/gpt-4o',
      systemPrompt: 'You are helpful.',
      photo: '',
    });
  });

  it('dispatches the update preserving the current isActive on submit', () => {
    render(<EditAIAgentModal agent={buildAgent({ isActive: false, name: '  Padded name  ' })} onClose={onClose} />);

    userEvent.click(screen.getByTestId('submit-edit-agent-form'));

    expect(mockDispatch).toHaveBeenCalledWith(
      updateAIAgent({
        id: 10,
        name: 'Padded name',
        providerId: 1,
        model: 'openai/gpt-4o',
        systemPrompt: 'You are helpful.',
        photo: null,
        isActive: false,
      }),
    );
    expect(onClose).toHaveBeenCalled();
  });
});

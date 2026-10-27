import * as React from 'react';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { EditAIAgentModal } from '../EditAIAgentModal';
import { updateAIAgent } from '../../../../redux/ai/slice';
import type { IAIAgent } from '../../../../api/ai/types';
import type { IAIAgentFormValues } from '../AIAgentForm/types';

jest.mock('../../../UI/BaseModal', () => ({
  BaseModal: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ModalHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('../AIAgentForm', () => ({
  AIAgentForm: ({
    initialValues,
    isSubmitting,
    onSubmit,
  }: {
    initialValues: IAIAgentFormValues;
    isSubmitting: boolean;
    onSubmit(values: IAIAgentFormValues): void;
  }) => (
    <button
      type="button"
      data-testid="submit-edit-agent-form"
      data-initial-values={JSON.stringify(initialValues)}
      data-submitting={String(isSubmitting)}
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

  const getUpdatePayload = () => {
    const [[action]] = mockDispatch.mock.calls as [[ReturnType<typeof updateAIAgent>]];

    return action.payload;
  };

  it('dispatches the update preserving the current isActive and closes only after success', () => {
    render(<EditAIAgentModal agent={buildAgent({ isActive: false, name: '  Padded name  ' })} onClose={onClose} />);

    userEvent.click(screen.getByTestId('submit-edit-agent-form'));

    expect(getUpdatePayload()).toEqual(
      expect.objectContaining({
        id: 10,
        name: 'Padded name',
        providerId: 1,
        model: 'openai/gpt-4o',
        systemPrompt: 'You are helpful.',
        photo: null,
        isActive: false,
      }),
    );
    expect(screen.getByTestId('submit-edit-agent-form')).toHaveAttribute('data-submitting', 'true');
    expect(onClose).not.toHaveBeenCalled();

    act(() => getUpdatePayload().onSuccess?.());

    expect(onClose).toHaveBeenCalled();
  });

  it('keeps the modal open with the draft when the update fails', () => {
    render(<EditAIAgentModal agent={buildAgent()} onClose={onClose} />);

    userEvent.click(screen.getByTestId('submit-edit-agent-form'));
    act(() => getUpdatePayload().onError?.());

    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByTestId('submit-edit-agent-form')).toHaveAttribute('data-submitting', 'false');
  });
});

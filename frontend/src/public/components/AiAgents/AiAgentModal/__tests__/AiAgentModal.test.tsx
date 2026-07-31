import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { loadAiModels } from '../../../../redux/actions';
import { IAiAgent, IAiModel } from '../../../../redux/aiAgents/types';
import { AiAgentModal } from '../AiAgentModal';

jest.mock('react-redux', () => ({
  connect: () => (component: unknown) => component,
  Provider: ({ children }: { children: React.ReactNode }) => children,
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

const dispatchMock = jest.fn();

const makeAgent = (overrides: Partial<IAiAgent> = {}): IAiAgent => ({
  id: 1,
  name: 'Analyst',
  modelSlug: 'vendor/model-a',
  systemPrompt: '',
  temperature: null,
  maxTokens: null,
  photo: null,
  isActive: true,
  ...overrides,
});

const mockModalState = ({
  editAgent = null,
  models = [],
}: {
  editAgent?: IAiAgent | null;
  models?: IAiModel[];
}) => {
  (useSelector as jest.Mock).mockImplementation((selector) =>
    selector({
      aiAgents: {
        editModal: { isOpen: true, editAgent },
        models: { isLoading: false, list: models },
      },
    }),
  );
};

describe('AiAgentModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(dispatchMock);
  });

  it('requests the model catalog when opened without one', () => {
    mockModalState({});

    render(<AiAgentModal />);

    expect(dispatchMock).toHaveBeenCalledWith(loadAiModels());
  });

  it('falls back to manual slug entry without a catalog', () => {
    mockModalState({});

    render(<AiAgentModal />);

    expect(screen.getByPlaceholderText('e.g. anthropic/claude-sonnet-4.5')).toBeInTheDocument();
    expect(screen.queryByText('Select a model')).not.toBeInTheDocument();
  });

  it('renders the model dropdown with the agent model selected', () => {
    mockModalState({
      editAgent: makeAgent(),
      models: [
        { slug: 'vendor/model-a', name: 'Alpha Model' },
        { slug: 'vendor/model-b', name: 'Beta Model' },
      ],
    });

    render(<AiAgentModal />);

    expect(dispatchMock).not.toHaveBeenCalledWith(loadAiModels());
    expect(screen.getByText('Alpha Model — vendor/model-a')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('e.g. anthropic/claude-sonnet-4.5')).not.toBeInTheDocument();
  });

  it('keeps a model missing from the catalog selectable', () => {
    mockModalState({
      editAgent: makeAgent({ modelSlug: 'vendor/retired-model' }),
      models: [{ slug: 'vendor/model-a', name: 'Alpha Model' }],
    });

    render(<AiAgentModal />);

    expect(screen.getByText('vendor/retired-model')).toBeInTheDocument();
  });
});

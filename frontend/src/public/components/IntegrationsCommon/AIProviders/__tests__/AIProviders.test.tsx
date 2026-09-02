import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { AIProviders } from '../AIProviders';
import { createAIProvider, deleteAIProvider, loadAIProviders } from '../../../../redux/ai/slice';
import { EAIVendor, IAIProvider } from '../../../../types/ai';

jest.mock('../../../UI', () => ({
  Tooltip: ({ children, content }: any) => <div data-testid="tooltip" data-content={content}>{children}</div>,
}));

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, disabled, type }: any) => (
    <button onClick={onClick} data-testid={testId} disabled={disabled} type={type}>
      {label}
    </button>
  ),
}));

jest.mock('../../../UI/Fields/InputField', () => ({
  InputField: ({ value, onChange, placeholder, 'data-testid': testId }: any) => (
    <input value={value} onChange={onChange} placeholder={placeholder} data-testid={testId} />
  ),
}));

jest.mock('../../../UI/Typeography/Header', () => ({
  Header: ({ children, className }: any) => <p className={className}>{children}</p>,
}));

jest.mock('../../../UI/Modal/Modal', () => ({
  Modal: ({ children, isOpen }: any) => (isOpen ? <div role="dialog">{children}</div> : null),
}));

const buildProvider = (overrides: Partial<IAIProvider> = {}): IAIProvider => ({
  id: 1,
  name: 'OpenRouter',
  baseUrl: 'https://openrouter.ai/api/v1',
  apiKeyPrefix: 'sk-or-v1-01234',
  vendor: EAIVendor.OpenRouter,
  isActive: true,
  usage: [],
  ...overrides,
});

describe('AIProviders', () => {
  const mockDispatch = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  const mockAIState = (providers: IAIProvider[], extra: object = {}) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: {
          providers: { isLoading: false, isLoaded: true, list: providers },
          agents: { isLoading: false, isLoaded: false, list: [] },
          models: { isLoading: false, providerId: null, list: [] },
          isSaving: false,
          ...extra,
        },
      }),
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    mockAIState([]);
  });

  it('loads providers on mount and shows the empty state', () => {
    render(<AIProviders />);

    expect(mockDispatch).toHaveBeenCalledWith(loadAIProviders());
    expect(screen.getByTestId('empty-ai-providers-message')).toBeInTheDocument();
  });

  it('renders the provider with its detected name, URL and masked key prefix', () => {
    mockAIState([buildProvider()]);

    render(<AIProviders />);

    expect(screen.getByText('OpenRouter')).toBeInTheDocument();
    expect(screen.getByText('https://openrouter.ai/api/v1')).toBeInTheDocument();
    expect(screen.getByText(/sk-or-v1-01234/)).toBeInTheDocument();
  });

  it('deletes an unused provider through the confirmation modal', () => {
    mockAIState([buildProvider()]);

    render(<AIProviders />);

    const deleteButton = screen.getByTestId('delete-ai-provider-1');
    expect(deleteButton).toBeEnabled();

    userEvent.click(deleteButton);
    userEvent.click(screen.getByTestId('confirm-delete-ai-provider'));

    expect(mockDispatch).toHaveBeenCalledWith(deleteAIProvider(1));
  });

  it('disables deletion for a provider used by agents and names them in the tooltip', () => {
    mockAIState([
      buildProvider({
        usage: [
          { id: 10, name: 'Research assistant' },
          { id: 11, name: 'Support bot' },
        ],
      }),
    ]);

    render(<AIProviders />);

    expect(screen.getByTestId('delete-ai-provider-1')).toBeDisabled();
    expect(screen.getByTestId('tooltip')).toHaveAttribute(
      'data-content',
      intlMock.formatMessage(
        { id: 'ai-providers.delete-disabled-tooltip' },
        { agents: 'Research assistant, Support bot' },
      ),
    );
    expect(screen.getByTestId('ai-provider-usage-1')).toHaveTextContent('Research assistant, Support bot');
  });

  it('creates a provider from the modal with trimmed base URL and key', () => {
    render(<AIProviders />);

    userEvent.click(screen.getByTestId('create-ai-provider-btn'));

    const submit = screen.getByTestId('submit-create-ai-provider');
    expect(submit).toBeDisabled();

    userEvent.type(screen.getByTestId('ai-provider-base-url-input'), '  https://openrouter.ai/api/v1  ');
    expect(submit).toBeDisabled();

    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), ' sk-or-v1-secret ');
    expect(submit).toBeEnabled();

    userEvent.click(submit);

    expect(mockDispatch).toHaveBeenCalledWith(
      createAIProvider({ baseUrl: 'https://openrouter.ai/api/v1', apiKey: 'sk-or-v1-secret' }),
    );
  });

  it('shows the loading state before the first response', () => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: {
          providers: { isLoading: true, isLoaded: false, list: [] },
          agents: { isLoading: false, isLoaded: false, list: [] },
          models: { isLoading: false, providerId: null, list: [] },
          isSaving: false,
        },
      }),
    );

    render(<AIProviders />);

    expect(screen.getByText(t('ai-providers.loading'))).toBeInTheDocument();
    expect(screen.queryByTestId('empty-ai-providers-message')).not.toBeInTheDocument();
  });
});

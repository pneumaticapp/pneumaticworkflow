import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { AIProviders } from '../AIProviders';
import { deleteAIProvider, loadAIProviders } from '../../../../redux/ai/slice';
import { EAIVendor, IAIProvider } from '../../../../types/ai';

jest.mock('../AIProvidersSkeleton', () => ({
  AIProvidersSkeleton: () => <div data-testid="ai-providers-skeleton" />,
}));

jest.mock('../../../UI', () => ({
  Tooltip: ({ children, content }: any) => (
    <div data-testid="tooltip" data-content={content}>
      {children}
    </div>
  ),
}));

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, disabled, type }: any) => (
    <button onClick={onClick} data-testid={testId} disabled={disabled} type={type}>
      {label}
    </button>
  ),
}));

jest.mock('../../../UI/Fields/InputField', () => {
  const { useField } = jest.requireActual('formik');

  return {
    FormikInputField: ({ name, 'data-testid': testId }: { name: string; 'data-testid'?: string }) => {
      const [field] = useField(name);

      return <input {...field} data-testid={testId} />;
    },
  };
});

jest.mock('../../../UI/DropdownList', () => {
  const { useField } = jest.requireActual('formik');

  return {
    FormikDropdownList: ({ name }: { name: string }) => {
      const [field] = useField(name);

      return <input {...field} data-testid="ai-provider-vendor-select" />;
    },
  };
});

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

  const mockAIState = (providers: IAIProvider[], extra: object = {}, status = 'succeeded') => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: {
          providers: { status, list: providers },
          createProvider: { status: 'idle', requestId: null },
          agents: { isLoading: false, list: [] },
          vendors: { isLoading: false, list: [] },
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

  it('opens the create modal on the add button', () => {
    render(<AIProviders />);

    expect(screen.queryByTestId('create-ai-provider-modal')).not.toBeInTheDocument();

    userEvent.click(screen.getByTestId('create-ai-provider-btn'));

    expect(screen.getByTestId('create-ai-provider-modal')).toBeInTheDocument();
  });

  it('shows the loading state before the first response', () => {
    mockAIState([], {}, 'loading');

    render(<AIProviders />);

    expect(screen.getByTestId('ai-providers-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('empty-ai-providers-message')).not.toBeInTheDocument();
  });

  it('shows a retry action rather than an empty state after loading fails', () => {
    mockAIState([], {}, 'failed');
    render(<AIProviders />);

    expect(screen.getByTestId('ai-providers-load-error')).toBeInTheDocument();
    expect(screen.queryByTestId('empty-ai-providers-message')).not.toBeInTheDocument();
    jest.clearAllMocks();
    userEvent.click(screen.getByRole('button', { name: intlMock.formatMessage({ id: 'ai-providers.retry' }) }));
    expect(mockDispatch).toHaveBeenCalledWith(loadAIProviders());
  });

  it('keeps existing providers visible after a failed refresh', () => {
    mockAIState([buildProvider()], {}, 'failed');
    render(<AIProviders />);

    expect(screen.getByTestId('ai-provider-1')).toBeInTheDocument();
    expect(screen.getByTestId('ai-providers-load-error')).toBeInTheDocument();
  });
});

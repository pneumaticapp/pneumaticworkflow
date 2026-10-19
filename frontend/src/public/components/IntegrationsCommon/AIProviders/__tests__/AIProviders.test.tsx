import * as React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { AIProviders } from '../AIProviders';
import { deleteAIProvider, loadAIProviders, openCreateAIProviderModal } from '../../../../redux/ai/slice';
import { EAIVendor } from '../../../../api/ai/types';
import type { IAIProvider } from '../../../../api/ai/types';

jest.mock('../../../UI/Tooltip', () => ({
  Tooltip: ({ children, content, disabled }: any) => (
    <div data-testid="tooltip" data-content={content} data-disabled={disabled}>
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

  const mockAIState = (providers: IAIProvider[], extra: object = {}, isLoading = false) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: {
          providers: { isLoading, list: providers },
          createProviderModal: { isOpen: false, isLoading: false },
          agents: { isLoading: false, list: [] },
          vendors: { isLoading: false, list: [] },
          models: { isLoading: false, providerId: null, list: [] },
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
    expect(
      screen.getByRole('region', { name: intlMock.formatMessage({ id: 'ai-providers.title' }) }),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(
      intlMock.formatMessage({ id: 'ai-providers.title' }),
    );
    expect(within(screen.getByRole('list')).getByRole('listitem')).toHaveAttribute('data-testid', 'ai-provider-1');
    expect(screen.getByRole('heading', { level: 3, name: 'OpenRouter' })).toBeInTheDocument();
    expect(screen.getByText(/sk-or-v1-01234/).tagName).toBe('CODE');
  });

  it('deletes an unused provider through the confirmation modal', async () => {
    mockAIState([buildProvider()]);

    render(<AIProviders />);

    const deleteButton = screen.getByTestId('delete-ai-provider-1');
    expect(deleteButton).toBeEnabled();
    expect(screen.getByTestId('tooltip')).toHaveAttribute('data-disabled', 'true');

    userEvent.click(deleteButton);
    const dialog = screen
      .getByRole('heading', { level: 2, name: intlMock.formatMessage({ id: 'ai-providers.delete-modal-title' }) })
      .closest('.modal-content') as HTMLElement;
    userEvent.click(
      within(dialog).getByRole('button', { name: intlMock.formatMessage({ id: 'ai-providers.delete' }) }),
    );

    expect(mockDispatch).toHaveBeenCalledWith(deleteAIProvider(1));
    await waitFor(() =>
      expect(
        screen.queryByRole('heading', { name: intlMock.formatMessage({ id: 'ai-providers.delete-modal-title' }) }),
      ).not.toBeInTheDocument(),
    );
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
    expect(screen.getByTestId('tooltip')).toHaveAttribute('data-disabled', 'false');
    expect(screen.getByTestId('tooltip')).toHaveAttribute(
      'data-content',
      intlMock.formatMessage(
        { id: 'ai-providers.delete-disabled-tooltip' },
        { agents: 'Research assistant, Support bot' },
      ),
    );
    expect(
      screen.getByText(
        intlMock.formatMessage({ id: 'ai-providers.usage' }, { agents: 'Research assistant, Support bot' }),
      ),
    ).toBeInTheDocument();
    userEvent.click(screen.getByTestId('delete-ai-provider-1'));
    expect(
      screen.queryByRole('heading', { name: intlMock.formatMessage({ id: 'ai-providers.delete-modal-title' }) }),
    ).not.toBeInTheDocument();
    expect(mockDispatch).not.toHaveBeenCalledWith(deleteAIProvider(1));
  });

  it('opens the create modal on the add button', () => {
    render(<AIProviders />);

    expect(screen.queryByTestId('create-ai-provider-modal')).not.toBeInTheDocument();

    userEvent.click(screen.getByTestId('create-ai-provider-btn'));

    expect(mockDispatch).toHaveBeenCalledWith(openCreateAIProviderModal());
  });

  it('renders the create modal when the store opens it', () => {
    mockAIState([], { createProviderModal: { isOpen: true, isLoading: false } });
    render(<AIProviders />);

    expect(screen.getByTestId('create-ai-provider-modal')).toBeInTheDocument();
  });

  it('shows the loading state before the first response', () => {
    mockAIState([], {}, true);

    render(<AIProviders />);

    expect(screen.getByTestId('ai-providers-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('empty-ai-providers-message')).not.toBeInTheDocument();
  });

  it('keeps existing providers visible without a skeleton during a refresh', () => {
    mockAIState([buildProvider()]);
    render(<AIProviders />);

    expect(screen.getByTestId('ai-provider-1')).toBeInTheDocument();
    expect(screen.queryByTestId('ai-providers-skeleton')).not.toBeInTheDocument();
  });
});

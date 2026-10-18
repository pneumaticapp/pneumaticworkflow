import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';
import { IntegrationsCommon } from '../IntegrationsCommon';
import { loadApiKeys, createApiKey, deleteApiKey, clearNewlyCreatedKey } from '../../../redux/actions';
import { copyToClipboard } from '../../../utils/helpers';
import { NotificationManager } from '../../UI/Notifications';

jest.mock('../../../utils/helpers', () => ({
  copyToClipboard: jest.fn(),
}));

jest.mock('../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, className, type }: any) => (
    <button onClick={onClick} data-testid={testId} className={className} type={type}>
      {label}
    </button>
  ),
}));

jest.mock('../../UI/Fields/InputField', () => ({
  InputField: ({ value, onChange, placeholder, 'data-testid': testId, autoFocus }: any) => (
    <input value={value} onChange={onChange} placeholder={placeholder} data-testid={testId} autoFocus={autoFocus} />
  ),
}));

jest.mock('../../UI/Typeography/Header', () => ({
  Header: ({ children, className }: any) => <p className={className}>{children}</p>,
}));

jest.mock('../../PageTitle/PageTitle', () => ({
  PageTitle: () => <div>Page Title</div>,
}));

jest.mock('../../UI/Modal/Modal', () => ({
  Modal: ({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) =>
    isOpen ? <div>{children}</div> : null,
}));

jest.mock('../../UI/Notifications', () => ({
  NotificationManager: { success: jest.fn() },
}));

jest.mock('../AIProviders', () => ({
  AIProviders: () => <section data-testid="ai-providers-section" />,
}));

const renderPage = () =>
  render(
    <IntlProvider locale="en-US" messages={enMessages}>
      <IntegrationsCommon />
    </IntlProvider>,
  );

describe('IntegrationsCommon', () => {
  const mockDispatch = jest.fn();
  const t = (id: keyof typeof enMessages) => enMessages[id];
  const TEXT = {
    loading: t('integrations.loading-api-key'),
    neverUsed: t('integrations.api-key-never-used'),
    deleteConfirm: t('integrations.delete-api-key-confirm'),
    createBtn: t('integrations.create-api-key'),
    doneBtn: t('integrations.api-key-done'),
    revokeBtn: t('integrations.api-key-revoke'),
  };

  beforeEach(() => {
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    (copyToClipboard as jest.Mock).mockClear();
    mockDispatch.mockClear();

    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) => {
      return selectorFn({
        integrations: {
          apiKeys: {
            data: [],
            isLoading: false,
            newlyCreatedKey: null,
          },
        },
      });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state correctly', () => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) => {
      return selectorFn({
        integrations: {
          apiKeys: { data: [], isLoading: true, newlyCreatedKey: null },
        },
      });
    });

    renderPage();
    expect(screen.getByText(TEXT.loading)).toBeInTheDocument();
    expect(mockDispatch).toHaveBeenCalledWith(loadApiKeys());
  });

  it('renders empty state correctly', () => {
    renderPage();
    expect(screen.getByTestId('empty-keys-message')).toBeInTheDocument();
    expect(screen.getByTestId('ai-providers-section')).toBeInTheDocument();
  });

  it('renders api keys list', () => {
    const mockKeys = [
      { id: 1, name: 'Key 1', prefix: 'pn_live_111', lastUsedAt: null },
      { id: 2, name: 'Key 2', prefix: 'pn_live_222', lastUsedAt: '2026-07-30T00:00:00Z' },
    ];

    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) => {
      return selectorFn({
        integrations: {
          apiKeys: { data: mockKeys, isLoading: false, newlyCreatedKey: null },
        },
      });
    });

    renderPage();

    expect(screen.getByTestId('api-keys-list')).toBeInTheDocument();
    expect(screen.getByText('Key 1')).toBeInTheDocument();
    expect(screen.getByText('pn_live_111••••••••')).toBeInTheDocument();
    expect(screen.getByText(TEXT.neverUsed)).toBeInTheDocument();

    expect(screen.getByText('Key 2')).toBeInTheDocument();
    expect(screen.getByText('pn_live_222••••••••')).toBeInTheDocument();
    expect(screen.getByText(/Last used:/)).toBeInTheDocument();
  });

  it('handles create api key flow', () => {
    renderPage();

    userEvent.click(screen.getByRole('button', { name: TEXT.createBtn }));
    expect(screen.getByTestId('create-key-modal')).toBeInTheDocument();

    const input = screen.getByTestId('api-key-name-input');
    userEvent.type(input, 'New Test Key');

    userEvent.click(screen.getByTestId('submit-create-key'));
    expect(mockDispatch).toHaveBeenCalledWith(createApiKey({ name: 'New Test Key' }));
    expect(screen.queryByTestId('create-key-modal')).not.toBeInTheDocument();
  });

  it('handles revoke key flow', () => {
    const mockKeys = [{ id: 1, name: 'Key 1', prefix: 'pn_live_111', lastUsedAt: null }];
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) => {
      return selectorFn({
        integrations: {
          apiKeys: { data: mockKeys, isLoading: false, newlyCreatedKey: null },
        },
      });
    });

    renderPage();

    userEvent.click(screen.getByRole('button', { name: TEXT.revokeBtn }));
    expect(screen.getByText(TEXT.deleteConfirm)).toBeInTheDocument();

    userEvent.click(screen.getByTestId('confirm-revoke-btn'));
    expect(mockDispatch).toHaveBeenCalledWith(deleteApiKey({ id: 1 }));
  });

  it('displays newly created key modal and handles copy', () => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) => {
      return selectorFn({
        integrations: {
          apiKeys: { data: [], isLoading: false, newlyCreatedKey: 'pn_live_secret_key_abc' },
        },
      });
    });

    renderPage();

    expect(screen.getByTestId('new-key-modal')).toBeInTheDocument();
    expect(screen.getByTestId('raw-key-value')).toHaveTextContent('pn_live_secret_key_abc');

    userEvent.click(screen.getByTestId('copy-inline-btn'));
    expect(copyToClipboard).toHaveBeenCalledWith('pn_live_secret_key_abc');
    expect(NotificationManager.success).toHaveBeenCalledWith({ message: 'integrations.api-key-copied' });

    userEvent.click(screen.getByRole('button', { name: TEXT.doneBtn }));
    expect(mockDispatch).toHaveBeenCalledWith(clearNewlyCreatedKey());
  });

  it('clears the key name when creation is cancelled', () => {
    renderPage();

    userEvent.click(screen.getByTestId('create-api-key-btn'));
    userEvent.type(screen.getByTestId('api-key-name-input'), 'Discarded key');
    userEvent.click(screen.getByTestId('cancel-create-key'));
    userEvent.click(screen.getByTestId('create-api-key-btn'));

    expect(screen.getByTestId('api-key-name-input')).toHaveValue('');
    expect(mockDispatch).not.toHaveBeenCalledWith(createApiKey({ name: 'Discarded key' }));
  });

  it('creates an unnamed key without an empty name', () => {
    renderPage();

    userEvent.click(screen.getByTestId('create-api-key-btn'));
    userEvent.click(screen.getByTestId('submit-create-key'));

    expect(mockDispatch).toHaveBeenCalledWith(createApiKey({ name: undefined }));
    expect(screen.queryByTestId('create-key-modal')).not.toBeInTheDocument();
  });

  it('cancels key revocation without deleting the key', () => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        integrations: {
          apiKeys: {
            data: [{ id: 1, name: 'Key 1', prefix: 'pn_live_111', lastUsedAt: null }],
            isLoading: false,
            newlyCreatedKey: null,
          },
        },
      }),
    );
    renderPage();

    userEvent.click(screen.getByTestId('revoke-1'));
    userEvent.click(screen.getByTestId('cancel-revoke-btn'));

    expect(screen.queryByTestId('revoke-key-modal')).not.toBeInTheDocument();
    expect(mockDispatch).not.toHaveBeenCalledWith(deleteApiKey({ id: 1 }));
  });

  it('clears the newly created key when the page is unmounted', () => {
    const { unmount } = renderPage();
    mockDispatch.mockClear();

    unmount();

    expect(mockDispatch).toHaveBeenCalledWith(clearNewlyCreatedKey());
  });
});

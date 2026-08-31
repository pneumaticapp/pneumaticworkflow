// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';
import { intlMock } from '../../__stubs__/intlMock';
import { IntegrationsCommon } from './IntegrationsCommon';
import {
  loadApiKeys,
  createApiKey,
  deleteApiKey,
  clearNewlyCreatedKey,
} from '../../redux/actions';
import { copyToClipboard } from '../../utils/helpers';



jest.mock('../../utils/helpers', () => ({
  copyToClipboard: jest.fn(),
}));

jest.mock('../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, className, type }: any) => (
    <button onClick={onClick} data-testid={testId} className={className} type={type}>
      {label}
    </button>
  ),
}));

jest.mock('../UI/Fields/InputField', () => ({
  InputField: ({ value, onChange, placeholder, 'data-testid': testId, autoFocus }: any) => (
    <input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      data-testid={testId}
      autoFocus={autoFocus}
    />
  ),
}));

jest.mock('../UI/Typeography/Header', () => ({
  Header: ({ children, className }: any) => (
    <p className={className}>{children}</p>
  ),
}));

jest.mock('../PageTitle/PageTitle', () => ({
  PageTitle: () => <div>Page Title</div>,
}));

describe('IntegrationsCommon', () => {
  const mockDispatch = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });
  const TEXT = {
    loading: t('integrations.loading-api-key'),
    neverUsed: t('integrations.api-key-never-used'),
    deleteConfirm: t('integrations.delete-api-key-confirm'),
    copied: t('integrations.api-key-copied'),
    createBtn: t('integrations.create-api-key'),
    doneBtn: t('integrations.api-key-done'),
    copyBtn: t('integrations.api-key-copy'),
    revokeBtn: t('integrations.api-key-revoke'),
    cancelBtn: t('integrations.cancel'),
  };

  beforeEach(() => {
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    (copyToClipboard as jest.Mock).mockClear();
    mockDispatch.mockClear();

    // Default mock state for useSelector
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

    render(<IntegrationsCommon />);
    expect(screen.getByText(TEXT.loading)).toBeInTheDocument();
    expect(mockDispatch).toHaveBeenCalledWith(loadApiKeys());
  });

  it('renders empty state correctly', () => {
    render(<IntegrationsCommon />);
    expect(screen.getByTestId('empty-keys-message')).toBeInTheDocument();
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

    render(<IntegrationsCommon />);
    
    expect(screen.getByTestId('api-keys-list')).toBeInTheDocument();
    expect(screen.getByText('Key 1')).toBeInTheDocument();
    expect(screen.getByText('pn_live_111••••••••')).toBeInTheDocument();
    expect(screen.getByText(TEXT.neverUsed)).toBeInTheDocument();

    expect(screen.getByText('Key 2')).toBeInTheDocument();
    expect(screen.getByText('pn_live_222••••••••')).toBeInTheDocument();
    expect(screen.getByText(/integrations.api-key-last-used/)).toBeInTheDocument();
  });

  it('handles create api key flow', () => {
    render(<IntegrationsCommon />);
    
    userEvent.click(screen.getByRole('button', { name: TEXT.createBtn }));
    expect(screen.getByTestId('create-key-modal')).toBeInTheDocument();

    const input = screen.getByTestId('api-key-name-input');
    userEvent.type(input, 'New Test Key');

    userEvent.click(screen.getByRole('button', { name: TEXT.createBtn }));
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

    render(<IntegrationsCommon />);

    // Click revoke (shows confirmation)
    userEvent.click(screen.getByRole('button', { name: TEXT.revokeBtn }));
    expect(screen.getByText(TEXT.deleteConfirm)).toBeInTheDocument();

    // Click confirm revoke
    userEvent.click(screen.getByRole('button', { name: TEXT.revokeBtn }));
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

    render(<IntegrationsCommon />);
    
    expect(screen.getByTestId('new-key-modal')).toBeInTheDocument();
    expect(screen.getByTestId('raw-key-value')).toHaveTextContent('pn_live_secret_key_abc');

    userEvent.click(screen.getByRole('button', { name: TEXT.copyBtn }));
    expect(copyToClipboard).toHaveBeenCalledWith('pn_live_secret_key_abc');
    expect(screen.getByRole('button', { name: TEXT.copied })).toBeInTheDocument();

    userEvent.click(screen.getByRole('button', { name: TEXT.doneBtn }));
    expect(mockDispatch).toHaveBeenCalledWith(clearNewlyCreatedKey());
  });
});

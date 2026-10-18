import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { CreateAIProviderModal } from '../CreateAIProviderModal';
import {
  closeCreateAIProviderModal,
  createAIProvider,
  createAIProviderByVendor,
  loadAIVendors,
} from '../../../../redux/ai/slice';
import type { IAIVendor } from '../../../../api/ai/types';

interface IMockButtonProps {
  label: string;
  onClick?: () => void;
  'data-testid'?: string;
  disabled?: boolean;
  type?: 'button' | 'submit';
}

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: ({ label, onClick, 'data-testid': testId, disabled, type }: IMockButtonProps) => (
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

jest.mock('../../../UI/Modal/Modal', () => ({
  Modal: ({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) =>
    isOpen ? <div role="dialog">{children}</div> : null,
}));

jest.mock('../../../UI/DropdownList', () => {
  const { useField } = jest.requireActual('formik');

  return {
    FormikDropdownList: ({
      name,
      options,
      'data-testid': testId,
    }: {
      name: string;
      options: { value?: string; label: React.ReactNode }[];
      'data-testid'?: string;
    }) => {
      const [field, , { setValue }] = useField(name);

      return (
        <select data-testid={testId} value={field.value} onChange={(event) => setValue(event.target.value)}>
          <option value="">Select a vendor</option>
          {options.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      );
    },
  };
});

const vendors: IAIVendor[] = [
  { slug: 'openrouter', name: 'OpenRouter' },
  { slug: 'openai', name: 'OpenAI' },
];

describe('CreateAIProviderModal', () => {
  const mockDispatch = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });
  let createProviderModalState: { isOpen: boolean; isLoading: boolean };

  const renderModal = () => render(<CreateAIProviderModal />);

  beforeEach(() => {
    jest.clearAllMocks();
    createProviderModalState = { isOpen: true, isLoading: false };
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: {
          vendors: { isLoading: false, list: vendors },
          createProviderModal: createProviderModalState,
        },
      }),
    );
  });

  it('loads vendors through the redux action on open', () => {
    renderModal();

    expect(mockDispatch).toHaveBeenCalledWith(loadAIVendors());
    expect(screen.getByRole('heading', { level: 2, name: t('ai-providers.create-modal-title') })).toBeInTheDocument();
  });

  it('creates a provider by vendor from the default tab', async () => {
    renderModal();

    expect(screen.getByText(t('ai-providers.connection-check-info'))).toBeInTheDocument();

    const submit = screen.getByTestId('submit-create-ai-provider');
    await waitFor(() => expect(submit).toBeDisabled());

    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), ' sk-or-v1-secret ');
    await waitFor(() => expect(submit).toBeDisabled());

    userEvent.selectOptions(screen.getByTestId('ai-provider-vendor-select'), 'openrouter');
    await waitFor(() => expect(submit).toBeEnabled());

    userEvent.click(submit);

    await waitFor(() =>
      expect(mockDispatch).toHaveBeenCalledWith(expect.objectContaining({ type: createAIProviderByVendor.type })),
    );
    const action = mockDispatch.mock.calls
      .map(([dispatched]) => dispatched)
      .find(({ type }) => type === createAIProviderByVendor.type);
    expect(action).toMatchObject({ payload: { vendor: 'openrouter', apiKey: 'sk-or-v1-secret' } });
    expect(mockDispatch).not.toHaveBeenCalledWith(closeCreateAIProviderModal());
  });

  it('creates a custom provider from the second tab', async () => {
    renderModal();

    userEvent.click(screen.getByText(t('ai-providers.tab-custom')));

    expect(screen.getByText(t('ai-providers.connection-check-info'))).toBeInTheDocument();

    const submit = screen.getByTestId('submit-create-ai-provider');
    await waitFor(() => expect(submit).toBeDisabled());

    userEvent.type(screen.getByTestId('ai-provider-name-input'), ' My provider ');
    userEvent.type(screen.getByTestId('ai-provider-base-url-input'), '  https://openrouter.ai/api/v1  ');
    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), ' sk-or-v1-secret ');
    await waitFor(() => expect(submit).toBeEnabled());

    userEvent.click(submit);

    await waitFor(() =>
      expect(mockDispatch).toHaveBeenCalledWith(expect.objectContaining({ type: createAIProvider.type })),
    );
    const action = mockDispatch.mock.calls
      .map(([dispatched]) => dispatched)
      .find(({ type }) => type === createAIProvider.type);
    expect(action).toMatchObject({
      payload: { name: 'My provider', baseUrl: 'https://openrouter.ai/api/v1', apiKey: 'sk-or-v1-secret' },
    });
    expect(mockDispatch).not.toHaveBeenCalledWith(closeCreateAIProviderModal());
  });

  it('shows the submit as loading while the provider is being created', async () => {
    const { rerender } = renderModal();
    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), 'secret');
    userEvent.selectOptions(screen.getByTestId('ai-provider-vendor-select'), 'openrouter');
    await waitFor(() => expect(screen.getByTestId('submit-create-ai-provider')).toBeEnabled());

    createProviderModalState = { isOpen: true, isLoading: true };
    rerender(<CreateAIProviderModal />);

    expect(screen.getByTestId('submit-create-ai-provider')).toBeDisabled();
  });

  it('keeps the draft and allows retry when the create request fails', async () => {
    const { rerender } = renderModal();
    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), 'secret');
    userEvent.selectOptions(screen.getByTestId('ai-provider-vendor-select'), 'openrouter');
    await waitFor(() => expect(screen.getByTestId('submit-create-ai-provider')).toBeEnabled());
    userEvent.click(screen.getByTestId('submit-create-ai-provider'));

    await waitFor(() =>
      expect(mockDispatch).toHaveBeenCalledWith(expect.objectContaining({ type: createAIProviderByVendor.type })),
    );
    createProviderModalState = { isOpen: true, isLoading: true };
    rerender(<CreateAIProviderModal />);
    createProviderModalState = { isOpen: true, isLoading: false };
    rerender(<CreateAIProviderModal />);

    expect(screen.getByTestId('ai-provider-api-key-input')).toHaveValue('secret');
    expect(screen.getByTestId('submit-create-ai-provider')).toBeEnabled();
  });

  it('closes through the store on cancel', () => {
    renderModal();

    userEvent.click(screen.getByTestId('cancel-create-ai-provider'));

    expect(mockDispatch).toHaveBeenCalledWith(closeCreateAIProviderModal());
  });
});

import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { CreateAIProviderModal } from '../CreateAIProviderModal';
import { createAIProvider, createAIProviderByVendor, loadAIVendors } from '../../../../redux/ai/slice';
import { IAIVendor } from '../../../../types/ai';

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

jest.mock('../../../UI/Typeography/Header', () => ({
  Header: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <p className={className}>{children}</p>
  ),
}));

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
  const mockOnClose = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  const renderModal = () => render(<CreateAIProviderModal isOpen onClose={mockOnClose} />);

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: {
          vendors: { isLoading: false, list: vendors },
          isSaving: false,
        },
      }),
    );
  });

  it('loads vendors through the redux action on open', () => {
    renderModal();

    expect(mockDispatch).toHaveBeenCalledWith(loadAIVendors());
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
      expect(mockDispatch).toHaveBeenCalledWith(
        createAIProviderByVendor({ vendor: 'openrouter', apiKey: 'sk-or-v1-secret' }),
      ),
    );
    expect(mockOnClose).toHaveBeenCalled();
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
      expect(mockDispatch).toHaveBeenCalledWith(
        createAIProvider({
          name: 'My provider',
          baseUrl: 'https://openrouter.ai/api/v1',
          apiKey: 'sk-or-v1-secret',
        }),
      ),
    );
    expect(mockOnClose).toHaveBeenCalled();
  });
});

import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { CreateAIProviderModal } from '../CreateAIProviderModal';
import { createAIProvider, createAIProviderByVendor } from '../../../../redux/ai/slice';
import { getAIVendors } from '../../../../api/ai';
import { IAIVendor } from '../../../../types/ai';

jest.mock('../../../../api/ai', () => ({
  getAIVendors: jest.fn(),
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

jest.mock('../../../UI/DropdownList', () => ({
  DropdownList: ({ options, onChange, 'data-testid': testId }: any) => (
    <select data-testid={testId} onChange={(e) => onChange({ value: e.target.value })}>
      <option value="">—</option>
      {options.map((option: any) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  ),
}));

const vendors: IAIVendor[] = [
  { slug: 'openrouter', name: 'OpenRouter' },
  { slug: 'openai', name: 'OpenAI' },
];

describe('CreateAIProviderModal', () => {
  const mockDispatch = jest.fn();
  const mockOnClose = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  const mockAIState = () => {
    (useSelector as unknown as jest.Mock).mockImplementation((selectorFn) =>
      selectorFn({
        ai: { isSaving: false },
      }),
    );
  };

  const renderModal = () => render(<CreateAIProviderModal isOpen onClose={mockOnClose} />);

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    (getAIVendors as jest.Mock).mockResolvedValue(vendors);
    mockAIState();
  });

  it('creates a provider by vendor from the default tab', async () => {
    renderModal();

    expect(screen.getByText(t('ai-providers.connection-check-info'))).toBeInTheDocument();

    const submit = screen.getByTestId('submit-create-ai-provider');
    expect(submit).toBeDisabled();

    await waitFor(() => expect(screen.getByTestId('ai-provider-vendor-select')).toBeInTheDocument());
    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), ' sk-or-v1-secret ');
    expect(submit).toBeDisabled();

    userEvent.selectOptions(screen.getByTestId('ai-provider-vendor-select'), 'openrouter');
    expect(submit).toBeEnabled();

    userEvent.click(submit);

    expect(mockDispatch).toHaveBeenCalledWith(
      createAIProviderByVendor({ vendor: 'openrouter', apiKey: 'sk-or-v1-secret' }),
    );
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('creates a custom provider from the second tab', async () => {
    renderModal();

    userEvent.click(screen.getByText(t('ai-providers.tab-custom')));

    expect(screen.getByText(t('ai-providers.connection-check-info'))).toBeInTheDocument();

    const submit = screen.getByTestId('submit-create-ai-provider');
    expect(submit).toBeDisabled();

    userEvent.type(screen.getByTestId('ai-provider-name-input'), ' My provider ');
    userEvent.type(screen.getByTestId('ai-provider-base-url-input'), '  https://openrouter.ai/api/v1  ');
    userEvent.type(screen.getByTestId('ai-provider-api-key-input'), ' sk-or-v1-secret ');
    expect(submit).toBeEnabled();

    userEvent.click(submit);

    expect(mockDispatch).toHaveBeenCalledWith(
      createAIProvider({
        name: 'My provider',
        baseUrl: 'https://openrouter.ai/api/v1',
        apiKey: 'sk-or-v1-secret',
      }),
    );
    expect(mockOnClose).toHaveBeenCalled();
  });
});

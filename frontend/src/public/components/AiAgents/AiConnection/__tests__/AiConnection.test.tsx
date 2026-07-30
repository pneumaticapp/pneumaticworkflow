import * as React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { removeAiConnection, saveAiConnection } from '../../../../redux/actions';
import { AiConnection } from '../AiConnection';

jest.mock('react-redux', () => ({
  connect: () => (component: unknown) => component,
  Provider: ({ children }: { children: React.ReactNode }) => children,
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

const dispatchMock = jest.fn();

const mockConnectionState = (connection: {
  isAvailable: boolean;
  isSaving: boolean;
  value: { id: number; baseUrl: string; apiKeyMask: string } | null;
}) => {
  (useSelector as jest.Mock).mockImplementation((selector) => selector({ aiAgents: { connection } }));
};

describe('AiConnection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(dispatchMock);
  });

  it('renders nothing when the connection endpoint is not available', () => {
    mockConnectionState({ isAvailable: false, isSaving: false, value: null });

    const { container } = render(<AiConnection />);

    expect(container).toBeEmptyDOMElement();
  });

  it('saves a trimmed key from the form', () => {
    mockConnectionState({ isAvailable: true, isSaving: false, value: null });

    render(<AiConnection />);
    const input = screen.getByPlaceholderText('sk-or-v1-...');
    fireEvent.change(input, { target: { value: '  sk-or-v1-secret  ' } });
    fireEvent.click(screen.getByText('Save key'));

    expect(dispatchMock).toHaveBeenCalledWith(saveAiConnection({ apiKey: 'sk-or-v1-secret' }));
  });

  it('shows the masked key with replace and remove actions', () => {
    mockConnectionState({
      isAvailable: true,
      isSaving: false,
      value: { id: 1, baseUrl: 'https://openrouter.ai/api/v1', apiKeyMask: 'sk-or-v1••••cdef' },
    });

    render(<AiConnection />);

    expect(screen.getByText('sk-or-v1••••cdef')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('sk-or-v1-...')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Remove'));
    expect(dispatchMock).toHaveBeenCalledWith(removeAiConnection());
  });

  it('opens the key form on replace', () => {
    mockConnectionState({
      isAvailable: true,
      isSaving: false,
      value: { id: 1, baseUrl: 'https://openrouter.ai/api/v1', apiKeyMask: 'sk-or-v1••••cdef' },
    });

    render(<AiConnection />);
    fireEvent.click(screen.getByText('Replace key'));

    expect(screen.getByPlaceholderText('sk-or-v1-...')).toBeInTheDocument();
  });
});

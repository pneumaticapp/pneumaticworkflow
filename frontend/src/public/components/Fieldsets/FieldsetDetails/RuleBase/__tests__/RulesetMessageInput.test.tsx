import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

import { RulesetMessageInput } from '../RulesetMessageInput';
import { intlMock } from '../../../../../__stubs__/intlMock';

describe('RulesetMessageInput component', () => {
  const mockOnChange = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders label and input with message value', () => {
    render(
      <RulesetMessageInput
        message="Custom error message"
        onChange={mockOnChange}
        isReadOnly={false}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.ruleset-message'))).toBeInTheDocument();

    const input = screen.getByDisplayValue('Custom error message');
    expect(input).toBeInTheDocument();
    expect(input).not.toBeDisabled();
  });

  it('calls onChange callback when user types in input', () => {
    render(
      <RulesetMessageInput
        message=""
        onChange={mockOnChange}
        isReadOnly={false}
      />,
    );

    const input = screen.getByPlaceholderText(formatMsg('fieldsets.ruleset-message-placeholder'));
    fireEvent.change(input, { target: { value: 'New message' } });

    expect(mockOnChange).toHaveBeenCalledTimes(1);
    expect(mockOnChange).toHaveBeenCalledWith('New message');
  });

  it('disables input when isReadOnly is true', () => {
    render(
      <RulesetMessageInput
        message="Read-only message"
        onChange={mockOnChange}
        isReadOnly={true}
      />,
    );

    const input = screen.getByDisplayValue('Read-only message');
    expect(input).toBeDisabled();
  });

  it('does not show error state when message is empty because message is optional', () => {
    render(
      <RulesetMessageInput
        message=""
        onChange={mockOnChange}
        isReadOnly={false}
      />,
    );

    const input = screen.getByPlaceholderText(formatMsg('fieldsets.ruleset-message-placeholder'));
    expect(input).not.toHaveClass('ruleset-message-input_error');
  });
});

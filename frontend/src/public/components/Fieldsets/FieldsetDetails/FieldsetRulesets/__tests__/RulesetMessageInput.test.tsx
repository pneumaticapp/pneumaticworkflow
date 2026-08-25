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

  it('renders input with current message and triggers onChange on typing', () => {
    render(
      <RulesetMessageInput
        message="Initial error message"
        onChange={mockOnChange}
        isReadOnly={false}
      />,
    );

    const input = screen.getByPlaceholderText(
      formatMsg('fieldsets.ruleset-message-placeholder'),
    );
    expect(input).toHaveValue('Initial error message');

    fireEvent.change(input, { target: { value: 'Updated error message' } });

    expect(mockOnChange).toHaveBeenCalledTimes(1);
    expect(mockOnChange).toHaveBeenCalledWith('Updated error message');
  });

  it('disables input when isReadOnly is true', () => {
    render(
      <RulesetMessageInput
        message="Read-only message"
        onChange={mockOnChange}
        isReadOnly={true}
      />,
    );

    const input = screen.getByPlaceholderText(
      formatMsg('fieldsets.ruleset-message-placeholder'),
    );
    expect(input).toBeDisabled();
  });
});

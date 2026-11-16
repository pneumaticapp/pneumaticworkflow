import * as React from 'react';
import { configure, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { GraphAutoArrangeButton } from '../GraphAutoArrangeButton';

configure({ testIdAttribute: 'data-test-id' });

describe('GraphAutoArrangeButton', () => {
  it('should stay disabled while the layout is the automatic one', () => {
    const onReset = jest.fn();

    render(<GraphAutoArrangeButton isActive={false} onReset={onReset} />);

    const button = screen.getByTestId('graph-auto-arrange');

    expect(button).toBeDisabled();

    userEvent.click(button);

    expect(onReset).not.toHaveBeenCalled();
  });

  it('should reset the layout once the user has moved a card', () => {
    const onReset = jest.fn();

    render(<GraphAutoArrangeButton isActive onReset={onReset} />);

    expect(screen.getByRole('button', { name: 'Auto-arrange' })).toBeEnabled();

    userEvent.click(screen.getByTestId('graph-auto-arrange'));

    expect(onReset).toHaveBeenCalledTimes(1);
  });
});

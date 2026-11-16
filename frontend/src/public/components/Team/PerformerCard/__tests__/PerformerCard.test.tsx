import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { PerformerCard } from '../PerformerCard';

jest.mock('rc-switch', () => ({ checked, disabled, onChange, 'data-testid': testId }: Record<string, any>) => (
  <input
    type="checkbox"
    data-testid={testId}
    checked={checked}
    disabled={disabled}
    onChange={(event) => onChange(event.target.checked)}
  />
));

describe('PerformerCard', () => {
  it('renders the avatar, name, name badge and description', () => {
    render(
      <PerformerCard
        avatar={<span data-testid="avatar" />}
        name="Ada Lovelace"
        nameBadge="Absent"
        description="ID 1"
        data-testid="card"
      />,
    );

    expect(screen.getByTestId('card')).toBeInTheDocument();
    expect(screen.getByTestId('avatar')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Ada LovelaceAbsent');
    expect(screen.getByText('ID 1')).toBeInTheDocument();
  });

  it('passes toggle changes to the caller', () => {
    const onChange = jest.fn();
    render(
      <PerformerCard
        avatar={null}
        name="Agent"
        toggle={{ label: 'Active', isChecked: false, onChange }}
        data-testid="card"
      />,
    );

    userEvent.click(screen.getByTestId('card-toggle'));

    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('shows the badge instead of the controls', () => {
    render(
      <PerformerCard
        avatar={null}
        name="Me"
        badge="Current user"
        toggle={{ label: 'Admin', isChecked: true, onChange: jest.fn() }}
        options={[{ label: 'Delete', onClick: jest.fn() }]}
        data-testid="card"
      />,
    );

    expect(screen.getByText('Current user')).toBeInTheDocument();
    expect(screen.queryByTestId('card-toggle')).not.toBeInTheDocument();
    expect(screen.queryByTestId('card-more')).not.toBeInTheDocument();
  });
});

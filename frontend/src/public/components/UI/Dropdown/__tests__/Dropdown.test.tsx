import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { Dropdown } from '../Dropdown';

describe('Dropdown', () => {
  it('opens, runs an option action, and closes through the universal base', () => {
    const onEdit = jest.fn();
    render(
      <Dropdown
        renderToggle={() => 'Actions'}
        options={[{ label: 'Edit', onClick: onEdit }]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('closes on Escape and restores focus to the toggle', () => {
    render(
      <Dropdown renderToggle={() => 'Actions'} options={[{ label: 'Edit' }]} />,
    );
    const toggle = screen.getByRole('button', { name: 'Actions' });

    fireEvent.click(toggle);
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(toggle).toHaveFocus();
  });
});

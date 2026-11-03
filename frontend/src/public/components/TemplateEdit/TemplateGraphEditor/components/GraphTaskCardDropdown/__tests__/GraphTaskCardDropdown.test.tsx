import * as React from 'react';
import { configure, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { GraphTaskCardDropdown } from '../GraphTaskCardDropdown';

configure({ testIdAttribute: 'data-test-id' });

describe('GraphTaskCardDropdown', () => {
  const openMenu = (): void => {
    userEvent.click(screen.getByRole('button', { name: 'Task actions' }));
  };

  it('should open the menu without triggering the card click', () => {
    const onCardClick = jest.fn();

    render(
      <div onClick={onCardClick}>
        <GraphTaskCardDropdown onEdit={jest.fn()} onDelete={jest.fn()} />
      </div>,
    );

    openMenu();

    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'Edit task' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'Delete' })).toBeInTheDocument();
    expect(onCardClick).not.toHaveBeenCalled();
  });

  it('should edit and close the menu', () => {
    const onEdit = jest.fn();
    render(<GraphTaskCardDropdown onEdit={onEdit} onDelete={jest.fn()} />);

    openMenu();
    userEvent.click(screen.getByRole('menuitem', { name: 'Edit task' }));

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('should require inline confirmation before deleting', () => {
    const onDelete = jest.fn();
    render(<GraphTaskCardDropdown onEdit={jest.fn()} onDelete={onDelete} />);

    openMenu();
    userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));

    expect(screen.getByText('Sure?')).toBeInTheDocument();
    expect(onDelete).not.toHaveBeenCalled();

    userEvent.click(screen.getByRole('button', { name: 'Yes' }));

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('should cancel deletion without closing the menu', () => {
    const onDelete = jest.fn();
    render(<GraphTaskCardDropdown onEdit={jest.fn()} onDelete={onDelete} />);

    openMenu();
    userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    userEvent.click(screen.getByRole('button', { name: 'No' }));

    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByRole('menuitem', { name: 'Delete' })).toBeInTheDocument();
  });

  it.each([
    ['outside click', () => fireEvent.mouseDown(document.body)],
    ['Escape', () => fireEvent.keyDown(document, { key: 'Escape' })],
  ])('should close and reset confirmation on %s', (_, closeMenu) => {
    render(<GraphTaskCardDropdown onEdit={jest.fn()} onDelete={jest.fn()} />);

    openMenu();
    userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    closeMenu();

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();

    openMenu();
    expect(screen.getByRole('menuitem', { name: 'Delete' })).toBeInTheDocument();
  });
});

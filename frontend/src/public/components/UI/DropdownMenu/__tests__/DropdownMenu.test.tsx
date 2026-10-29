import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { DropdownMenu } from '../DropdownMenu';
import type { TDropdownMenuOption } from '../types';
import { enMessages } from '../../../../lang/locales/en_US';

const renderMenu = (options: TDropdownMenuOption[], props: Partial<React.ComponentProps<typeof DropdownMenu>> = {}) =>
  render(
    <IntlProvider locale="en-US" messages={enMessages}>
      <div data-testid="outside">outside</div>
      <DropdownMenu
        options={options}
        renderToggle={(isOpen) => <span>{isOpen ? 'Close menu' : 'Open menu'}</span>}
        {...props}
      />
    </IntlProvider>,
  );

const getMenu = () => screen.getAllByRole('menu', { hidden: true })[0];

describe('DropdownMenu', () => {
  it('opens on toggle click and closes on outside click and Escape', () => {
    renderMenu([{ label: 'Edit', onClick: jest.fn() }]);
    const toggle = screen.getByRole('button', { name: 'Open menu' });

    expect(getMenu()).toHaveAttribute('aria-hidden', 'true');
    userEvent.click(toggle);
    expect(getMenu()).toHaveAttribute('aria-hidden', 'false');
    expect(toggle).toHaveAttribute('aria-expanded', 'true');

    userEvent.click(screen.getByTestId('outside'));
    expect(getMenu()).toHaveAttribute('aria-hidden', 'true');

    userEvent.click(toggle);
    fireEvent.keyDown(screen.getByRole('menuitem', { name: 'Edit' }), { key: 'Escape' });
    expect(getMenu()).toHaveAttribute('aria-hidden', 'true');
    expect(toggle).toHaveFocus();
  });

  it('calls the option handler with a close callback and closes the menu', () => {
    const onClick = jest.fn();
    renderMenu([{ label: 'Edit', onClick }]);

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    userEvent.click(screen.getByRole('menuitem', { name: 'Edit' }));

    expect(onClick).toHaveBeenCalledWith(expect.any(Function));
    expect(getMenu()).toHaveAttribute('aria-hidden', 'true');
  });

  it('does not open when disabled', () => {
    renderMenu([{ label: 'Edit', onClick: jest.fn() }], { isDisabled: true });

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));

    expect(getMenu()).toHaveAttribute('aria-hidden', 'true');
  });

  it('asks for confirmation before running a confirmable option', () => {
    const onClick = jest.fn();
    renderMenu([{ label: 'Delete', onClick, withConfirmation: true, color: 'red' }]);

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    expect(onClick).not.toHaveBeenCalled();

    userEvent.click(screen.getByRole('button', { name: enMessages['dropdown.yes'] }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('toggles a submenu and runs its options', () => {
    const onSubOptionClick = jest.fn();
    renderMenu([{ label: 'Return to', subOptions: [{ label: 'Step 1', onClick: onSubOptionClick }] }]);

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    const submenuToggle = screen.getByRole('menuitem', { name: 'Return to' });
    expect(submenuToggle).toHaveAttribute('aria-expanded', 'false');

    userEvent.click(submenuToggle);
    expect(submenuToggle).toHaveAttribute('aria-expanded', 'true');

    userEvent.click(screen.getByRole('menuitem', { name: 'Step 1' }));
    expect(onSubOptionClick).toHaveBeenCalledTimes(1);
    expect(getMenu()).toHaveAttribute('aria-hidden', 'true');
  });

  it('opens a submenu beside its row and keeps the root menu in place', () => {
    renderMenu([{ label: 'Return to', subOptions: [{ label: 'Step 1' }] }]);

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    userEvent.click(screen.getByRole('menuitem', { name: 'Return to' }));

    const [rootMenu, submenu] = screen.getAllByRole('menu');

    expect(submenu.className).toContain('dropdown-menu_submenu');
    expect(rootMenu.className).not.toContain('dropdown-menu_submenu');
  });

  it('opens a submenu to the left when it does not fit on the right', () => {
    const clientWidthSpy = jest.spyOn(document.documentElement, 'clientWidth', 'get').mockReturnValue(1000);
    const rectSpy = jest
      .spyOn(HTMLElement.prototype, 'getBoundingClientRect')
      .mockReturnValue({ right: 1200 } as DOMRect);
    renderMenu([{ label: 'Return to', subOptions: [{ label: 'Step 1' }] }]);

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    const submenuToggle = screen.getByRole('menuitem', { name: 'Return to' });
    userEvent.click(submenuToggle);

    expect(submenuToggle.parentElement?.className).toContain('submenu_left');

    rectSpy.mockReturnValue({ right: 800 } as DOMRect);
    userEvent.click(submenuToggle);
    userEvent.click(submenuToggle);

    expect(submenuToggle.parentElement?.className).not.toContain('submenu_left');
    clientWidthSpy.mockRestore();
    rectSpy.mockRestore();
  });

  it('moves focus with arrows and leaves keys typed in a nested input alone', () => {
    renderMenu([
      { label: 'Edit', onClick: jest.fn() },
      { label: 'Add users', customSubOption: <input aria-label="Search users" /> },
    ]);

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    fireEvent.keyDown(getMenu(), { key: 'ArrowDown' });
    expect(screen.getByRole('menuitem', { name: 'Edit' })).toHaveFocus();

    userEvent.click(screen.getByRole('menuitem', { name: 'Add users' }));
    const search = screen.getByRole('textbox', { name: 'Search users' });
    search.focus();
    fireEvent.keyDown(search, { key: 'ArrowDown' });
    fireEvent.keyDown(search, { key: 'Escape' });

    expect(search).toHaveFocus();
    expect(getMenu()).toHaveAttribute('aria-hidden', 'false');
  });

  it('stops click propagation to parent handlers', () => {
    const onParentClick = jest.fn();
    render(
      <IntlProvider locale="en-US" messages={enMessages}>
        <div role="presentation" onClick={onParentClick}>
          <DropdownMenu options={[{ label: 'Edit', onClick: jest.fn() }]} renderToggle={() => 'Open menu'} />
        </div>
      </IntlProvider>,
    );

    userEvent.click(screen.getByRole('button', { name: 'Open menu' }));

    expect(onParentClick).not.toHaveBeenCalled();
  });
});

import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../../lang/locales/en_US';
import { Dropdown } from '../Dropdown';

import surfaceStyles from '../../DropdownSurface/DropdownSurface.css';
import styles from '../Dropdown.css';

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

  it('uses the universal surface and resets a wide submenu after the root closes', () => {
    render(
      <Dropdown
        renderToggle={() => 'Actions'}
        options={[{
          label: 'More',
          subOptions: [
            { label: 'First action', size: 'lg' },
            { label: 'Second action', size: 'lg' },
          ],
        }]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));

    const rootMenu = screen.getByRole('menu');
    expect(rootMenu).toHaveClass(surfaceStyles['dropdown-surface'], styles['dropdown-menu_with-submenu']);

    fireEvent.click(screen.getByRole('button', { name: 'More' }));

    expect(screen.getAllByRole('menu')[1]).toHaveClass(styles['dropdown-menu_wide']);

    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));

    expect(screen.getAllByRole('menu')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'More' })).toHaveAttribute('aria-expanded', 'false');
  });

  it('collapses the submenu again after a nested option is chosen', () => {
    const onNested = jest.fn();
    render(
      <Dropdown
        renderToggle={() => 'Actions'}
        options={[{ label: 'More', subOptions: [{ label: 'Nested action', onClick: onNested }] }]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));
    fireEvent.click(screen.getByRole('button', { name: 'More' }));
    fireEvent.click(screen.getByRole('button', { name: 'Nested action' }));

    expect(onNested).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));

    expect(screen.getAllByRole('menu')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'More' })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('button', { name: 'Nested action' })).not.toBeInTheDocument();
  });

  it('closes every level when a deeply nested option is chosen', () => {
    const onLeaf = jest.fn();
    render(
      <Dropdown
        renderToggle={() => 'Actions'}
        options={[{
          label: 'Level one',
          subOptions: [{ label: 'Level two', subOptions: [{ label: 'Leaf action', onClick: onLeaf }] }],
        }]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));
    fireEvent.click(screen.getByRole('button', { name: 'Level one' }));
    fireEvent.click(screen.getByRole('button', { name: 'Level two' }));
    fireEvent.click(screen.getByRole('button', { name: 'Leaf action' }));

    expect(onLeaf).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));

    expect(screen.getByRole('button', { name: 'Level one' })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('button', { name: 'Level two' })).not.toBeInTheDocument();
  });

  it('uses the wide surface for root custom content', () => {
    render(
      <Dropdown
        renderToggle={() => 'Custom content'}
        options={{ label: 'Custom', customSubOption: <div>Content</div> }}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Custom content' }));

    expect(screen.getByRole('menu')).toHaveClass(styles['dropdown-menu_wide']);
  });

  it('confirms an action and closes the menu', () => {
    const onDelete = jest.fn();
    render(
      <IntlProvider locale="en" messages={enMessages}>
        <Dropdown
          renderToggle={() => 'Actions'}
          options={[{ label: 'Delete', withConfirmation: true, onClick: onDelete }]}
        />
      </IntlProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Actions' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'No' }));

    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Yes' }));

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});

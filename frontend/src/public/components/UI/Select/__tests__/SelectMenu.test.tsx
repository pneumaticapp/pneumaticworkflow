import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { SelectMenu } from '../SelectMenu';
import { ETaskListSorting } from '../../../../types/tasks';
import { enMessages } from '../../../../lang/locales/en_US';

describe('SelectMenu', () => {
  const ACTIVE_LABEL = 'Newest first';
  const INACTIVE_LABEL = 'Oldest first';
  const OVERDUE_LABEL = 'Overdue first';
  const onChange = jest.fn();

  const renderSelectMenu = () =>
    render(
      <IntlProvider locale="en" messages={enMessages}>
        <SelectMenu
          activeValue={ETaskListSorting.DateDesc}
          values={Object.values(ETaskListSorting)}
          onChange={onChange}
        />
      </IntlProvider>,
    );

  const getMenuItem = (name: string) => screen.getByRole('menuitem', { name, hidden: true });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the active value in the button and all values in the menu with the active one marked', () => {
    renderSelectMenu();

    expect(screen.getByRole('button', { name: ACTIVE_LABEL })).toBeInTheDocument();
    const menuItems = screen.getAllByRole('menuitem', { hidden: true });
    expect(menuItems[0]).toHaveTextContent(INACTIVE_LABEL);
    expect(menuItems[1]).toHaveTextContent(ACTIVE_LABEL);
    expect(menuItems[2]).toHaveTextContent(OVERDUE_LABEL);
    expect(menuItems[0]).not.toHaveClass('value-item__disabled');
    expect(menuItems[1]).toHaveClass('value-item__disabled');
    expect(menuItems[2]).not.toHaveClass('value-item__disabled');
  });

  it('calls onChange with the item value when an inactive item is clicked', () => {
    renderSelectMenu();

    userEvent.click(getMenuItem(INACTIVE_LABEL));

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(ETaskListSorting.DateAsc);
  });

  it('does not call onChange when the active item is clicked', () => {
    renderSelectMenu();

    userEvent.click(getMenuItem(ACTIVE_LABEL));

    expect(onChange).not.toHaveBeenCalled();
  });
});

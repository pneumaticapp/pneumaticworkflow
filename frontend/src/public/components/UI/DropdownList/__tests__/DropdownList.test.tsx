import * as React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { DropdownList } from '../DropdownList';

jest.mock('react-perfect-scrollbar', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const OPTIONS = [
  { value: 'date', label: 'By date' },
  { value: 'name', label: 'By name' },
];

const TestIcon = () => <svg data-testid="control-icon" />;

describe('DropdownList compact control', () => {
  it('renders the selected label with an icon and picks an option, closing the menu', () => {
    const onChange = jest.fn();
    render(
      <DropdownList
        controlSize="sm"
        controlVariant="accent"
        Icon={TestIcon}
        options={OPTIONS}
        value={OPTIONS[0]}
        onChange={onChange}
      />,
    );

    const control = screen.getByRole('button', { name: 'By date' });
    expect(screen.getByTestId('control-icon')).toBeInTheDocument();

    userEvent.click(control);
    userEvent.click(screen.getByText('By name'));

    expect(onChange).toHaveBeenCalledWith(OPTIONS[1], expect.objectContaining({ action: 'select-option' }));
    expect(screen.queryByText('By name')).not.toBeInTheDocument();
  });

  it('does not open when disabled', () => {
    render(<DropdownList controlSize="sm" isDisabled options={OPTIONS} value={OPTIONS[0]} onChange={jest.fn()} />);

    const control = screen.getByRole('button', { name: 'By date' });
    expect(control).toBeDisabled();

    fireEvent.click(control);

    expect(screen.queryByText('By name')).not.toBeInTheDocument();
  });

  it('renders the menu into a portal target when one is passed', () => {
    render(
      <DropdownList
        controlSize="sm"
        options={OPTIONS}
        value={OPTIONS[0]}
        onChange={jest.fn()}
        menuPortalTarget={document.body}
        menuPosition="fixed"
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'By date' }));

    expect(document.body.querySelector('.react-select__menu-portal')).toContainElement(screen.getByText('By name'));
  });
});

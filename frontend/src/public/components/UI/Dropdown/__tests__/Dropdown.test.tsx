import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dropdown } from '../Dropdown';

jest.mock('react-outside-click-handler', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));

jest.mock('reactstrap', () => {
  const actual = jest.requireActual('reactstrap');
  return {
    ...actual,
    DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

describe('Dropdown', () => {
  it('supports label as a render prop function receiving closeDropdown', () => {
    const renderLabelMock = jest.fn((closeDropdown?: () => void) => (
      <span
        role="button"
        tabIndex={0}
        onClick={closeDropdown}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            closeDropdown?.();
          }
        }}
      >
        Render Prop Option
      </span>
    ));

    const options = [
      {
        mapKey: 'custom-option',
        label: renderLabelMock,
        onClick: jest.fn(),
      },
    ];

    render(<Dropdown options={options} renderToggle={() => <span>Open</span>} />);

    userEvent.click(screen.getByText('Open'));

    expect(renderLabelMock).toHaveBeenCalledWith(expect.any(Function));
    expect(screen.getByText('Render Prop Option')).toBeInTheDocument();

    userEvent.click(screen.getByText('Render Prop Option'));

    expect(renderLabelMock).toHaveBeenCalled();
  });
});

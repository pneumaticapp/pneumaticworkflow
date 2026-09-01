import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dropdown } from '../Dropdown';

jest.mock('react-outside-click-handler', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../Dropdown.css', () => new Proxy({}, { get: (_t, k) => String(k) }));

describe('Dropdown', () => {
  it('supports label as a render prop function receiving closeDropdown', () => {
    const renderLabelMock = jest.fn((closeDropdown?: () => void) => (
      <button type="button" onClick={closeDropdown}>
        Render Prop Option
      </button>
    ));

    const options = [
      {
        mapKey: 'custom-option',
        label: renderLabelMock,
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

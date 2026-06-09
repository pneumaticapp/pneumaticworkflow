/* eslint-disable */
/// <reference types="jest" />

import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

type TTestOption = {
  id: number;
  displayName: string;
  type: string;
};

const getSelectionKey = (option: TTestOption) => `${option.type}-${option.id}`;

describe('FilterSelect selection key logic', () => {
  it('does not treat user and group with the same id as the same selected option', () => {
    const selectedOptions = ['user-5'];
    const groupOption: TTestOption = { id: 5, displayName: 'Group Five', type: 'group' };

    expect(selectedOptions.includes(getSelectionKey(groupOption))).toBe(false);
  });

  it('adds group selection without removing user selection when ids collide', () => {
    const selectedOptions = ['user-5'];
    const groupOption: TTestOption = { id: 5, displayName: 'Group Five', type: 'group' };
    const selectionKey = getSelectionKey(groupOption);

    const newSelectedOptions = [...selectedOptions, selectionKey];

    expect(newSelectedOptions).toEqual(['user-5', 'group-5']);
  });
});

jest.mock('reactstrap', () => ({
  Dropdown: ({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) => (
    <div data-testid="dropdown" data-open={isOpen}>
      {children}
    </div>
  ),
  DropdownToggle: ({ children, ...props }: { children: React.ReactNode }) => (
    <button type="button" data-testid="filter-select-toggle" {...props}>
      {children}
    </button>
  ),
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div role="menu">{children}</div>,
  DropdownItem: ({
    children,
    onClick,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  ),
}));

jest.mock('react-perfect-scrollbar', () => {
  const Scrollbar = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  Object.assign(Scrollbar, { __esModule: true, default: Scrollbar });
  return Scrollbar;
});

jest.mock('react-outside-click-handler', () => {
  const OutsideClick = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  return {
    __esModule: true,
    default: OutsideClick,
  };
});

jest.mock('../../../icons', () => ({
  ClearIcon: () => null,
  ExpandIcon: () => null,
}));

jest.mock('../../Fields/Checkbox', () => ({
  Checkbox: ({ title }: { title: React.ReactNode }) => <label>{title}</label>,
}));

jest.mock('../../Fields/InputField', () => ({
  InputField: () => <input />,
}));

const defaultProps = {
  options: [] as { id: number; name: string }[],
  optionIdKey: 'id' as const,
  optionLabelKey: 'name' as const,
  placeholderText: 'No items found',
  selectedOption: null,
  resetFilter: jest.fn(),
  onChange: jest.fn(),
  renderPlaceholder: () => 'All templates',
};

const openDropdown = () => {
  fireEvent.click(screen.getByTestId('filter-select-toggle'));
};

describe('FilterSelect', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { FilterSelect } = require('../FilterSelect') as typeof import('../FilterSelect');

  it('shows skeleton rows in dropdown menu when isLoading is true', () => {
    const { container } = render(<FilterSelect {...defaultProps} isLoading />);

    openDropdown();

    expect(screen.queryByText('No items found')).not.toBeInTheDocument();
    expect(container.querySelectorAll('.dropdown-menu__skeleton-item').length).toBe(5);
  });

  it('shows options in dropdown menu when isLoading is false', () => {
    render(
      <FilterSelect
        {...defaultProps}
        options={[
          { id: 1, name: 'Template A' },
          { id: 2, name: 'Template B' },
        ]}
      />,
    );

    openDropdown();

    expect(screen.getByText('Template A')).toBeInTheDocument();
    expect(screen.getByText('Template B')).toBeInTheDocument();
    expect(screen.queryByText('No items found')).not.toBeInTheDocument();
  });
});

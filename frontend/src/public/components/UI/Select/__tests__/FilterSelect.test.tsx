import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { FilterSelect } from '../FilterSelect';

jest.mock('react-perfect-scrollbar', () => ({ children }: { children: React.ReactNode }) => <div>{children}</div>);
jest.mock('../../../icons', () => ({
  ClearIcon: () => null,
  ExpandIcon: () => null,
}));
jest.mock('../../Fields/InputField', () => ({ InputField: () => <input /> }));

type TTestOption = {
  id: number;
  displayName: string;
  type: string;
};

const getSelectionKey = (option: TTestOption) => `${option.type}-${option.id}`;
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
const openDropdown = () => fireEvent.click(screen.getByRole('button', { name: 'All templates' }));

describe('FilterSelect selection key logic', () => {
  it('does not treat user and group with the same id as the same selected option', () => {
    const selectedOptions = ['user-5'];
    const groupOption: TTestOption = { id: 5, displayName: 'Group Five', type: 'group' };

    expect(selectedOptions.includes(getSelectionKey(groupOption))).toBe(false);
  });

  it('adds group selection without removing user selection when ids collide', () => {
    const selectedOptions = ['user-5'];
    const groupOption: TTestOption = { id: 5, displayName: 'Group Five', type: 'group' };

    expect([...selectedOptions, getSelectionKey(groupOption)]).toEqual(['user-5', 'group-5']);
  });
});

describe('FilterSelect', () => {
  it('shows skeleton rows while loading', () => {
    const { container } = render(<FilterSelect {...defaultProps} isLoading />);

    openDropdown();

    expect(screen.queryByText('No items found')).not.toBeInTheDocument();
    expect(container.querySelectorAll('.dropdown-menu__skeleton-item')).toHaveLength(5);
  });

  it('shows options after loading', () => {
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
  });
});

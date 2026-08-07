import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FilterSelect } from '../FilterSelect';

jest.mock('react-perfect-scrollbar', () => ({ children }: { children: React.ReactNode }) => <div>{children}</div>);
jest.mock('../../../icons', () => ({
  ClearIcon: () => null,
  ExpandIcon: () => null,
}));
jest.mock('../../Fields/InputField', () => ({
  InputField: ({ fieldSize, onClear, ...props }: React.InputHTMLAttributes<HTMLInputElement> & {
    fieldSize?: string;
    onClear?(): void;
  }) => <input {...props} />,
}));

type TTestOption = {
  id: number;
  displayName: string;
  type: string;
};

const getSelectionKey = (option: TTestOption) => `${option.type}-${option.id}`;
const commonProps = {
  options: [] as { id: number; name: string }[],
  optionIdKey: 'id' as const,
  optionLabelKey: 'name' as const,
  placeholderText: 'No items found',
  resetFilter: jest.fn(),
  onChange: jest.fn(),
  renderPlaceholder: () => 'All templates',
};
const defaultProps = { ...commonProps, selectedOption: null };
const openDropdown = () => fireEvent.click(screen.getByRole('button', { name: 'All templates' }));

describe('FilterSelect', () => {
  beforeEach(() => jest.clearAllMocks());

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

  it('focuses search when the dropdown opens', () => {
    render(
      <FilterSelect
        {...defaultProps}
        isSearchShown
        searchPlaceholder="Search templates"
      />,
    );

    expect(screen.queryByPlaceholderText('Search templates')).not.toBeInTheDocument();

    openDropdown();

    expect(screen.getByPlaceholderText('Search templates')).toHaveFocus();
  });

  it('selects a multiple option once when its checkbox label is clicked', () => {
    const onChange = jest.fn();
    const options: TTestOption[] = [
      { id: 5, displayName: 'User Five', type: 'user' },
      { id: 5, displayName: 'Group Five', type: 'group' },
    ];

    render(
      <FilterSelect
        {...commonProps}
        options={options}
        optionLabelKey="displayName"
        isMultiple
        selectedOptions={['user-5']}
        getOptionSelectionKey={getSelectionKey}
        onChange={onChange}
      />,
    );
    openDropdown();

    userEvent.click(screen.getByText('Group Five'));

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(['user-5', 'group-5'], options);
  });

  it('runs Select All once and checks the actual option keys', () => {
    const onChange = jest.fn();
    render(
      <FilterSelect
        {...commonProps}
        options={[{ id: 1, name: 'One' }, { id: 2, name: 'Two' }]}
        isMultiple
        selectedOptions={[1, 99]}
        selectAllLabel="Select all"
        onChange={onChange}
      />,
    );
    openDropdown();

    const selectAll = screen.getByRole('menuitemcheckbox', { name: 'Select all' });
    expect(selectAll).toHaveAttribute('aria-checked', 'false');

    userEvent.click(screen.getByText('Select all'));

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith([1, 2], [{ id: 1, name: 'One' }, { id: 2, name: 'Two' }]);
  });

  it('shows only the empty state when search has no matches', () => {
    render(
      <FilterSelect
        {...commonProps}
        options={[{ id: 1, name: 'Template A' }]}
        selectedOption={1}
        noValueLabel="Reset templates"
        isSearchShown
        searchPlaceholder="Search templates"
      />,
    );
    openDropdown();

    userEvent.type(screen.getByPlaceholderText('Search templates'), 'missing');

    expect(screen.getByText('No items found')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Reset templates' })).not.toBeInTheDocument();
  });
});

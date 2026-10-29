import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Select } from '../Select';
import { getEnumSelectProps } from '../../../../utils/getEnumSelectProps';

jest.mock('react-perfect-scrollbar', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const OPTIONS = [
  { value: 'date', label: 'By date' },
  { value: 'name', label: 'By name' },
];

const TestIcon = () => <svg data-testid="control-icon" />;

describe('Select compact control', () => {
  it('renders the selected label with an icon and picks an option, closing the menu', () => {
    const onChange = jest.fn();
    render(
      <Select
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
    render(<Select controlSize="sm" isDisabled options={OPTIONS} value={OPTIONS[0]} onChange={jest.fn()} />);

    const control = screen.getByRole('button', { name: 'By date' });
    expect(control).toBeDisabled();

    fireEvent.click(control);

    expect(screen.queryByText('By name')).not.toBeInTheDocument();
  });

  it('selects an option rendered into a portal target', () => {
    const onChange = jest.fn();
    render(
      <Select
        controlSize="sm"
        options={OPTIONS}
        value={OPTIONS[0]}
        onChange={onChange}
        menuPortalTarget={document.body}
        menuPosition="fixed"
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'By date' }));
    const option = screen.getByText('By name');
    expect(document.body.querySelector('.react-select__menu-portal')).toContainElement(option);

    userEvent.click(option);

    expect(onChange).toHaveBeenCalledWith(OPTIONS[1], expect.objectContaining({ action: 'select-option' }));
  });

  it('shows a clear button instead of the arrow when onClear is passed', () => {
    const onClear = jest.fn();
    const onChange = jest.fn();
    const { rerender } = render(<Select controlSize="sm" isMulti options={OPTIONS} value={[]} onChange={onChange} />);
    expect(screen.queryByRole('button', { name: 'Clear selected options' })).not.toBeInTheDocument();

    rerender(
      <Select controlSize="sm" isMulti options={OPTIONS} value={[OPTIONS[1]]} onChange={onChange} onClear={onClear} />,
    );
    userEvent.click(screen.getByRole('button', { name: 'Clear selected options' }));

    expect(onClear).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('By date')).not.toBeInTheDocument();
  });

  it('renders checked checkboxes for selected options and keeps a multi menu open', () => {
    const onChange = jest.fn();
    render(
      <Select controlSize="sm" title="Sorting" isMulti options={OPTIONS} value={[OPTIONS[1]]} onChange={onChange} />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Sorting' }));
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.map((checkbox) => (checkbox as HTMLInputElement).checked)).toEqual([false, true]);

    userEvent.click(screen.getByText('By date'));

    expect(onChange).toHaveBeenCalledWith([OPTIONS[1], OPTIONS[0]], expect.anything());
    expect(screen.getByText('By date')).toBeInTheDocument();
  });

  it('shows skeleton rows instead of options while loading', () => {
    render(<Select controlSize="sm" title="Templates" isLoading options={OPTIONS} onChange={jest.fn()} />);

    userEvent.click(screen.getByRole('button', { name: 'Templates' }));

    expect(screen.queryByText('By name')).not.toBeInTheDocument();
    expect(document.querySelectorAll('.select-sm__skeleton')).toHaveLength(5);
  });

  it('renders custom control content instead of the pill', () => {
    render(
      <Select
        controlSize="sm"
        controlContent={<span>Pick fieldset</span>}
        options={OPTIONS}
        value={null}
        onChange={jest.fn()}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Pick fieldset' }));

    expect(screen.getByText('By name')).toBeInTheDocument();
  });

  it('renders grouped options under their headings', () => {
    render(
      <Select
        controlSize="sm"
        title={<span>Tasks</span>}
        isMulti
        options={[
          { label: 'Onboarding', options: [OPTIONS[0]] },
          { label: 'Offboarding', options: [OPTIONS[1]] },
        ]}
        value={[]}
        onChange={jest.fn()}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Tasks' }));

    expect(screen.getByText('Onboarding')).toBeInTheDocument();
    expect(screen.getByText('Offboarding')).toBeInTheDocument();
    expect(screen.getAllByRole('checkbox')).toHaveLength(2);
  });

  it('keeps the same control element while the menu opens', () => {
    render(<Select controlSize="sm" title="Sorting" options={OPTIONS} value={OPTIONS[0]} onChange={jest.fn()} />);
    const control = screen.getByRole('button', { name: 'Sorting' });

    userEvent.click(control);

    expect(screen.getByText('By name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sorting' })).toBe(control);
  });

  it('does not show the search unless isSearchable is passed with a sorting select', () => {
    render(
      <Select
        controlSize="sm"
        title="Sorting"
        {...getEnumSelectProps(['date', 'name'], 'date', jest.fn(), (({ id }: { id: string }) => id) as never)}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Sorting' }));

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('keeps the search text after ticking an option in a multi select', () => {
    render(
      <Select controlSize="sm" title="Users" isMulti isSearchable options={OPTIONS} value={[]} onChange={jest.fn()} />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Users' }));
    userEvent.type(screen.getByRole('textbox'), 'name');
    userEvent.click(screen.getByText('By name'));

    expect(screen.getByRole('textbox')).toHaveValue('name');
  });

  it('renders single-select options without checkboxes', () => {
    render(<Select controlSize="sm" title="Sorting" options={OPTIONS} value={OPTIONS[0]} onChange={jest.fn()} />);

    userEvent.click(screen.getByRole('button', { name: 'Sorting' }));

    expect(screen.getByText('By name')).toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(document.querySelector('.react-select__menu-list.is-multi')).not.toBeInTheDocument();
  });

  it('closes the compact menu on Escape from the search', () => {
    render(<Select controlSize="sm" title="Users" isSearchable options={OPTIONS} value={null} onChange={jest.fn()} />);

    userEvent.click(screen.getByRole('button', { name: 'Users' }));
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Escape', code: 'Escape', keyCode: 27 });

    expect(screen.queryByText('By name')).not.toBeInTheDocument();
  });

  it('selects the focused option with Enter from a portalled search without submitting the form', () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn((event: React.FormEvent) => event.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <Select
          controlSize="sm"
          title="Users"
          isSearchable
          options={OPTIONS}
          value={null}
          onChange={onChange}
          menuPortalTarget={document.body}
        />
      </form>,
    );

    userEvent.click(screen.getByRole('button', { name: 'Users' }));
    const search = screen.getByRole('textbox');
    userEvent.type(search, 'name');
    fireEvent.keyDown(search, { key: 'Enter', code: 'Enter', keyCode: 13 });

    expect(onChange).toHaveBeenCalledWith(OPTIONS[1], expect.objectContaining({ action: 'select-option' }));
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('searches options with element labels without searchByText', () => {
    render(
      <Select
        controlSize="sm"
        title="Steps"
        isSearchable
        options={[{ value: 'a', label: <span>Alpha</span> }]}
        value={null}
        onChange={jest.fn()}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Steps' }));
    userEvent.type(screen.getByRole('textbox'), 'al');

    expect(screen.getByRole('textbox')).toHaveValue('al');
    expect(screen.queryByText('Alpha')).not.toBeInTheDocument();
  });

  it('filters options by searchByText', () => {
    render(
      <Select
        controlSize="sm"
        title="Users"
        isSearchable
        options={[
          { value: '1', label: 'Ada', searchByText: 'ada lovelace' },
          { value: '2', label: 'Alan', searchByText: 'alan turing' },
        ]}
        onChange={jest.fn()}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Users' }));
    userEvent.type(screen.getByRole('textbox'), 'turing');

    expect(screen.queryByText('Ada')).not.toBeInTheDocument();
    expect(screen.getByText('Alan')).toBeInTheDocument();
  });
});

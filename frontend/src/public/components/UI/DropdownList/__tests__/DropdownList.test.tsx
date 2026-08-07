import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { getFormattedDropdownOption } from '../../../TemplateEdit/TaskForm/Conditions/utils/getFormattedDropdownOption';
import { DropdownList } from '../DropdownList';
import surfaceStyles from '../../DropdownSurface/DropdownSurface.css';
import controlStyles from '../../DropdownControl/DropdownControl.css';
import listStyles from '../DropdownList.css';
import optionStyles from '../DropdownOption.css';

const option = { label: 'Default option', value: 'default' };
const openMenu = (name: string) => fireEvent.click(screen.getByRole('button', { name }));

describe('DropdownList', () => {
  it('renders default options with the universal option component', () => {
    render(<DropdownList options={[option]} value={option} title="Pick a value" />);

    openMenu('Pick a value');

    const menuOption = screen
      .getAllByText(option.label)
      .find((element) => element.classList.contains(optionStyles['dropdown-option']));

    expect(menuOption).toHaveClass(
      optionStyles['dropdown-option'],
      optionStyles['dropdown-option_selected'],
    );
  });

  it('renders compact dropdowns with the universal control', () => {
    render(<DropdownList controlSize="sm" title="Add performer" options={[option]} />);

    expect(screen.getByText('Add performer')).toHaveClass(controlStyles['dropdown-control__value']);
  });

  it('renders condition options with the same universal styles', () => {
    render(<div>{getFormattedDropdownOption({ label: 'Condition option', isSelected: true })}</div>);

    expect(screen.getByText('Condition option')).toHaveClass(
      optionStyles['dropdown-option'],
      optionStyles['dropdown-option_selected'],
    );
  });

  it('renders the menu on the universal surface and keeps a caller menu class', () => {
    const { container } = render(
      <DropdownList options={[option]} title="Pick a value" menuClassName="caller-menu" />,
    );

    openMenu('Pick a value');

    expect(container.querySelector('.caller-menu')).toHaveClass(
      surfaceStyles['dropdown-surface'],
      'caller-menu',
    );
  });

  it('selects a single option and closes the menu', () => {
    const onChange = jest.fn();
    render(<DropdownList options={[option]} title="Pick a value" onChange={onChange} />);

    openMenu('Pick a value');
    fireEvent.click(screen.getByRole('option', { name: option.label }));

    expect(onChange).toHaveBeenCalledWith(option, { action: 'select-option', option });
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('keeps a single select value selected when it is picked again', () => {
    const onChange = jest.fn();
    render(<DropdownList options={[option]} value={option} title="Pick a value" onChange={onChange} />);

    openMenu('Pick a value');
    fireEvent.click(screen.getByRole('option', { name: option.label }));

    expect(onChange).toHaveBeenCalledWith(option, { action: 'select-option', option });
  });

  it('toggles selection and keeps the menu open for multi select', () => {
    const onChange = jest.fn();
    render(
      <DropdownList
        isMulti
        options={[option]}
        value={[option]}
        title="Pick values"
        onChange={onChange}
      />,
    );

    openMenu('Pick values');
    fireEvent.click(screen.getByRole('option', { name: option.label }));

    expect(onChange).toHaveBeenCalledWith([], { action: 'deselect-option', option });
    expect(screen.getByRole('menu')).toBeInTheDocument();
  });

  it('filters options by the in-menu search', () => {
    render(
      <DropdownList
        isSearchable
        title="Pick a value"
        options={[option, { label: 'Another option', value: 'another' }]}
      />,
    );

    openMenu('Pick a value');
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'another' } });

    expect(screen.getByRole('option', { name: 'Another option' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: option.label })).not.toBeInTheDocument();
  });

  it('renders grouped options under their headings', () => {
    render(
      <DropdownList
        title="Pick a value"
        options={[{ label: 'System events', options: [option] }]}
      />,
    );

    openMenu('Pick a value');

    expect(screen.getByText('System events')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: option.label })).toBeInTheDocument();
  });

  it('runs an option action instead of selecting it', () => {
    const onClick = jest.fn();
    const onChange = jest.fn();
    render(
      <DropdownList
        title="Pick a value"
        options={[{ label: 'Invite a teammate', value: 'invite', onClick }]}
        onChange={onChange}
      />,
    );

    openMenu('Pick a value');
    fireEvent.click(screen.getByRole('option', { name: 'Invite a teammate' }));

    expect(onClick).toHaveBeenCalledTimes(1);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('renders a static menu without a control', () => {
    render(<DropdownList staticMenu options={[option]} />);

    expect(screen.getByRole('option', { name: option.label })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Pick/ })).not.toBeInTheDocument();
  });

  it('shows the error message and marks the control', () => {
    const { container } = render(
      <DropdownList options={[option]} label="Role" errorMessage="Role is required" />,
    );

    expect(screen.getByText('Role is required')).toBeInTheDocument();
    expect(container.querySelector(`.${listStyles['dropdown-list__control_error']}`)).toBeInTheDocument();
  });

  it('keeps static-menu options inert when disabled', () => {
    const onChange = jest.fn();
    render(<DropdownList staticMenu isDisabled options={[option]} onChange={onChange} />);

    const menuOption = screen.getByRole('option', { name: option.label });
    expect(menuOption).toBeDisabled();

    fireEvent.click(menuOption);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('falls back to a default empty-state message', () => {
    render(<DropdownList isSearchable title="Pick a value" options={[option]} />);

    openMenu('Pick a value');
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'nothing matches' } });

    expect(screen.getByText('No options')).toBeInTheDocument();
  });
});

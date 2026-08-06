import React from 'react';
import { render, screen } from '@testing-library/react';

import { ConditionDropdownOption } from '../../../TemplateEdit/TaskForm/Conditions/ConditionDropdownOption';
import { DropdownList } from '../DropdownList';
import controlStyles from '../../DropdownControl/DropdownControl.css';
import optionStyles from '../DropdownOption.css';

const option = { label: 'Default option', value: 'default' };

describe('DropdownList options', () => {
  it('renders default UI options with the universal option component', () => {
    render(
      <DropdownList
        menuIsOpen
        isSearchable={false}
        options={[option]}
        value={option}
      />,
    );

    const menuOption = screen
      .getAllByText(option.label)
      .find((element) => element.classList.contains(optionStyles['dropdown-option']));

    expect(menuOption).toHaveClass(
      optionStyles['dropdown-option'],
      optionStyles['dropdown-option_selected'],
    );
  });

  it('renders compact dropdowns with the universal control', () => {
    render(
      <DropdownList
        controlSize="sm"
        title="Add performer"
        isSearchable={false}
        options={[option]}
      />,
    );

    expect(screen.getByText('Add performer')).toHaveClass(controlStyles['dropdown-control__value']);
  });

  it('renders condition options with the same universal styles', () => {
    render(<ConditionDropdownOption label="Condition option" isSelected />);

    expect(screen.getByText('Condition option')).toHaveClass(
      optionStyles['dropdown-option'],
      optionStyles['dropdown-option_selected'],
    );
  });
});

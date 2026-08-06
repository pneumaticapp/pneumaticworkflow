import React from 'react';
import { render, screen } from '@testing-library/react';

import { ConditionDropdownOption } from '../../../TemplateEdit/TaskForm/Conditions/ConditionDropdownOption';
import { DropdownList } from '../DropdownList';
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

  it('renders condition options with the same universal styles', () => {
    render(<ConditionDropdownOption label="Condition option" isSelected />);

    expect(screen.getByText('Condition option')).toHaveClass(
      optionStyles['dropdown-option'],
      optionStyles['dropdown-option_selected'],
    );
  });
});

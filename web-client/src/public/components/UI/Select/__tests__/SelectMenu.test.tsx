import * as React from 'react';
import { shallow } from 'enzyme';
import { DropdownItem } from 'reactstrap';

import { SelectMenu } from '../SelectMenu';
import { ETaskListSorting } from '../../../../types/tasks';

const mockProps = {
  activeValue: ETaskListSorting.DateDesc,
  values: Object.values(ETaskListSorting),
  onChange: jest.fn(),
};

describe('SelectMenu', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });
  it('корректно рендерится', () => {
    const wrapper = shallow(<SelectMenu {...mockProps}/>);

    expect(wrapper).toMatchSnapshot();
  });
  it('при клике на элемент вызывает onChange, если значение не активно', () => {
    const wrapper = shallow(<SelectMenu {...mockProps}/>);

    wrapper.find(DropdownItem).at(0).simulate('click');

    expect(mockProps.onChange).toHaveBeenCalledWith(ETaskListSorting.DateAsc);
  });
  it('при клике на элемент не вызывает onChange, если значение активно', () => {
    const wrapper = shallow(<SelectMenu {...mockProps}/>);

    wrapper.find(DropdownItem).at(1).simulate('click');

    expect(mockProps.onChange).not.toHaveBeenCalled();
  });
});

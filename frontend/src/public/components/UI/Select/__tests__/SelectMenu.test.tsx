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
  it('renders correctly', () => {
    const wrapper = shallow(<SelectMenu {...mockProps}/>);

    expect(wrapper).toMatchSnapshot();
  });
  it('clicking on the element calls onChange if the value is inactive', () => {
    const wrapper = shallow(<SelectMenu {...mockProps}/>);

    wrapper.find(DropdownItem).at(0).simulate('click');

    expect(mockProps.onChange).toHaveBeenCalledWith(ETaskListSorting.DateAsc);
  });
  it('clicking on the element does not call onChange if the value is active', () => {
    const wrapper = shallow(<SelectMenu {...mockProps}/>);

    wrapper.find(DropdownItem).at(1).simulate('click');

    expect(mockProps.onChange).not.toHaveBeenCalled();
  });
});

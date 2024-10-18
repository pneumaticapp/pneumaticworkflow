import * as React from 'react';
import { shallow } from 'enzyme';

import { SideModalCard } from '../SideModalCard';

const mockProps = {
  onClick: jest.fn(),
};

describe('SideModalCard', () => {
  it('calls onClick when card is clicked', () => {
    const wrapper = shallow(<SideModalCard {...mockProps} />);
    const card = wrapper.find('[role="button"]');
    card.simulate('click');

    expect(mockProps.onClick).toHaveBeenCalled();
  });
});

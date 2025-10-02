import * as React from 'react';
import { shallow } from 'enzyme';

import { MenuIcon } from '../MenuIcon';

describe('Menu Icon', () => {
  it('renders correctly.', () => {
    const wrapper = shallow(<MenuIcon />);

    expect(wrapper).toMatchSnapshot();
  });
});

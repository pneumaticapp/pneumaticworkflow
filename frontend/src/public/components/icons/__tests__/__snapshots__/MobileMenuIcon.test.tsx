import * as React from 'react';
import { shallow } from 'enzyme';

import { MobileMenuIcon } from '../../MobileMenuIcon';

describe('Menu Icon', () => {
  it('renders correctly.', () => {
    const wrapper = shallow(<MobileMenuIcon />);

    expect(wrapper).toMatchSnapshot();
  });
});

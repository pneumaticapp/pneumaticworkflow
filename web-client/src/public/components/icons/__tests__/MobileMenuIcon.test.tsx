/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { shallow } from 'enzyme';

import { MobileMenuIcon } from '../MobileMenuIcon';

describe('Mobile Menu Icon', () => {
  it('renders correctly.', () => {
    const wrapper = shallow(<MobileMenuIcon />);

    expect(wrapper).toMatchSnapshot();
  });
});

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { shallow } from 'enzyme';

import { MobileMenuIcon } from '../MobileMenuIcon';

describe('Mobile Menu Icon', () => {
  it('корректно рендерится', () => {
    const wrapper = shallow(<MobileMenuIcon />);

    expect(wrapper).toMatchSnapshot();
  });
});

import * as React from 'react';
import { shallow } from 'enzyme';

import { MobileMenuIcon } from '../../MobileMenuIcon';

describe('Menu Icon', () => {
  it('корректно рендерится', () => {
    const wrapper = shallow(<MobileMenuIcon />);

    expect(wrapper).toMatchSnapshot();
  });
});

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { shallow } from 'enzyme';

import { MenuIcon } from '../MenuIcon';

describe('Menu Icon', () => {
  it('корректно рендерится', () => {
    const wrapper = shallow(<MenuIcon />);

    expect(wrapper).toMatchSnapshot();
  });
});

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { shallow } from 'enzyme';

import { LogoCircle } from '../LogoCircle';

const mockProps = {
  size: 96,
  className: 'test',
  fillSecondary: '#000',
  fillPrimary: '#ccc',
};

describe('IconCircle', () => {
  it('renders with default props', () => {
    const wrapper = shallow(<LogoCircle />);

    expect(wrapper).toMatchSnapshot();
  });
  it('renders with non-default props', () => {
    const wrapper = shallow(<LogoCircle {...mockProps} />);

    expect(wrapper).toMatchSnapshot();
  });
});

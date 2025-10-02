/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { shallow } from 'enzyme';

import { GoogleProfile } from '../GoogleProfile';

const mockProps = {
  photo: '/mock/google/photo.jpg',
  firstName: 'Google',
  lastName: 'Profile',
  email: 'google@pneumatic.app',
};

describe('GoogleProfile', () => {
  it('renders correctly with all the data', () => {
    const wrapper = shallow(<GoogleProfile {...mockProps}/>);

    expect(wrapper).toMatchSnapshot();
  });
  it('returns null if there is no email', () => {
    const wrapper = shallow(<GoogleProfile {...mockProps} email=""/>);

    expect(wrapper.html()).toBeNull();
  });
});

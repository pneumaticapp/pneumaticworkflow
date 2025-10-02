import * as React from 'react';
import { shallow } from 'enzyme';

import { Avatar } from '../Avatar';
import styles from '../Avatar.css';


describe('Avatar', () => {
  it('renders image', () => {
    const url = '/some/image.png';
    const user = {
      firstName: '',
      lastName: '',
      photo: url,
      email: '',
    }
    const wrapper = shallow(<Avatar user={user} />);

    expect(wrapper.find('img').prop('src')).toEqual(url);
  });

  it('renders initials', () => {
    const firstName = 'Test';
    const lastName = 'User';
    const email = "test@test.com"
    const photo = "";
    const user = {
      firstName,
      lastName,
      photo,
      email,
    }
    const wrapper = shallow(
      <Avatar
        user={user}
      />,
    );

    const avatarElement = wrapper.find(`.${styles['avatar']}`);

    expect(avatarElement.text()).toEqual('TU');
  });

  it('does not render initials if no name passed', () => {
    const user = {
      firstName: '',
      lastName: '',
      photo: '',
      email: '',
    }

    const wrapper = shallow(<Avatar user={user} />);

    const avatarElement = wrapper.find(`.${styles['avatar']}`);

    expect(avatarElement.text()).toEqual('');
  });
});

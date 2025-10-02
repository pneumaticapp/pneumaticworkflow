import * as React from 'react';
import { shallow } from 'enzyme';

import { Users, IUsersProps } from '../Users';
import { mockLastNameUsers } from '../../../../__stubs__/users';
import { EUserListSorting } from '../../../../types/user';
import { TeamUser } from '../TeamUser';

const mockProps: IUsersProps = {
  currentUserId: 0,
  fetchUsers: jest.fn(),
  loadChangeUserAdmin: jest.fn(),
  openModal: jest.fn(),
  users: mockLastNameUsers,
  userListSorting: EUserListSorting.NameAsc,
  openTeamInvitesPopup: jest.fn(),
  setGeneralLoaderVisibility: jest.fn(),
  trialEnded: null,
  loadMicrosoftInvites: jest.fn(),
};

describe('Team', () => {
  it('rendered correctly', () => {
    const wrapper = shallow(<Users {...mockProps} />);

    expect(wrapper).toMatchSnapshot();
  });
  it('rendered correctly with descending sorting', () => {
    const wrapper = shallow(<Users {...mockProps} sorting={EUserListSorting.NameDesc} />);

    expect(wrapper).toMatchSnapshot();
  });
  it('correcltly reacts on user id', () => {
    const wrapper = shallow(<Users {...mockProps} />);

    expect(wrapper.find(TeamUser).at(0).props().isCurrentUser).toBe(true);
    expect(wrapper.find(TeamUser).at(2).props().isCurrentUser).toBe(false);
  });
});

import * as React from 'react';
import { shallow } from 'enzyme';

import { Users } from '../Users';
import { IUsersProps } from '../types';
import { mockLastNameUsers } from '../../../../__stubs__/users';
import { EUserListSorting } from '../../../../types/user';
import { TeamUser } from '../TeamUser';
import { CreateUserModal } from '../CreateUserModal';
import { NotificationManager } from '../../../UI/Notifications';

const mockProps: IUsersProps = {
  currentUserId: 0,
  fetchUsers: jest.fn(),
  loadChangeUserAdmin: jest.fn(),
  loadChangeUserManager: jest.fn(),
  openModal: jest.fn(),
  users: mockLastNameUsers,
  userListSorting: EUserListSorting.NameAsc,
  openTeamInvitesPopup: jest.fn(),
  setGeneralLoaderVisibility: jest.fn(),
  trialEnded: null,
  loadInvitesUsers: jest.fn(),
  loadChangeUserReports: jest.fn(),
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
  it('shows feedback while AI agent persistence is unavailable', () => {
    const warningSpy = jest.spyOn(NotificationManager, 'warning').mockImplementation();
    const wrapper = shallow(<Users {...mockProps} />);

    wrapper.find(CreateUserModal).props().onCreateAIAgent?.({
      firstName: 'Ada',
      lastName: 'Agent',
      position: 'Support',
      model: 'openai',
      endpoint: 'https://api.example.com',
      apiKey: 'secret',
      systemPrompt: '',
      avatar: '',
    });

    expect(warningSpy).toHaveBeenCalledWith({
      message: 'team.create-ai-agent-modal.backend-unavailable',
    });
  });

  it('correcltly reacts on user id', () => {
    const wrapper = shallow(<Users {...mockProps} />);

    expect(wrapper.find(TeamUser).at(0).props().isCurrentUser).toBe(true);
    expect(wrapper.find(TeamUser).at(2).props().isCurrentUser).toBe(false);
  });
});

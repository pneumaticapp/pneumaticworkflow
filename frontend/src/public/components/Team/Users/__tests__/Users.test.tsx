import * as React from 'react';
import { shallow } from 'enzyme';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Users } from '../Users';
import { TeamUser } from '../TeamUser';
import { TeamAgent } from '../TeamAgent';
import { TeamUserSkeleton } from '../../TeamUserSkeleton';
import { generateUser, mockLastNameUsers } from '../../../../__stubs__/users';
import { EUserListSorting } from '../../../../types/user';
import { EAIVendor } from '../../../../types/ai';
import type { IAIAgent, IAIProvider } from '../../../../types/ai';
import type { TUserListItem } from '../../../../types/user';
import { loadAIAgents, loadAIProviders } from '../../../../redux/ai/slice';
import { teamFetchStarted } from '../../../../redux/accounts/slice';
import { loadInvitesUsers } from '../../../../redux/team/slice';

jest.mock('../DeleteTeamUserPopup', () => ({
  DeleteTeamUserPopupContainer: () => null,
}));

jest.mock('../AddGuestsBanner', () => ({
  AddGuestsBanner: () => null,
}));

jest.mock('../CreatePerformerModal', () => ({
  CreatePerformerModal: () => null,
}));

jest.mock('../VacationSettingsModal', () => ({
  VacationSettingsModal: () => null,
}));

jest.mock('../../../PageTitle', () => ({
  PageTitle: () => null,
}));

jest.mock('../TeamUser', () => ({
  TeamUser: () => <div data-testid="team-user-card" />,
}));

jest.mock('../TeamAgent', () => ({
  TeamAgent: () => <div data-testid="team-agent-card" />,
}));

const buildProvider = (overrides: Partial<IAIProvider> = {}): IAIProvider => ({
  id: 1,
  name: 'OpenRouter',
  baseUrl: 'https://openrouter.ai/api/v1',
  apiKeyPrefix: 'sk-or',
  vendor: EAIVendor.OpenRouter,
  isActive: true,
  usage: [],
  ...overrides,
});

const buildAgent = (overrides: Partial<IAIAgent> = {}): IAIAgent => ({
  id: 10,
  name: 'Research assistant',
  photo: null,
  isActive: true,
  providerId: 1,
  model: 'openai/gpt-4o',
  systemPrompt: 'You are helpful.',
  ...overrides,
});

interface IMockStateParams {
  users?: TUserListItem[];
  agents?: IAIAgent[];
  providers?: IAIProvider[];
  isUsersLoading?: boolean;
  areAgentsLoading?: boolean;
}

describe('Users', () => {
  const mockDispatch = jest.fn();

  const mockState = ({
    users = mockLastNameUsers,
    agents = [],
    providers = [buildProvider()],
    isUsersLoading = false,
    areAgentsLoading = false,
  }: IMockStateParams = {}) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selector) =>
      selector({
        authUser: {
          id: 0,
          account: { isSubscribed: true, billingPlan: 'premium' },
        },
        accounts: {
          team: { list: users, isLoading: isUsersLoading },
          userListSorting: EUserListSorting.NameAsc,
          isCreateUserModalOpen: false,
        },
        ai: {
          agents: { isLoading: areAgentsLoading, list: agents },
          providers: { isLoading: false, list: providers },
          isSaving: false,
        },
      }),
    );
  };

  const renderUsers = (userListSorting = EUserListSorting.NameAsc) =>
    shallow(<Users userListSorting={userListSorting} />);

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    mockState();
  });

  it('rendered correctly', () => {
    const wrapper = renderUsers();

    expect(wrapper).toMatchSnapshot();
  });

  it('rendered correctly with descending sorting', () => {
    const wrapper = renderUsers(EUserListSorting.NameDesc);

    expect(wrapper).toMatchSnapshot();
  });

  it('rendered correctly with agents in the list', () => {
    mockState({ agents: [buildAgent()] });
    const wrapper = renderUsers();

    expect(wrapper).toMatchSnapshot();
  });

  it('correctly reacts on user id', () => {
    const wrapper = renderUsers();

    expect(wrapper.find(TeamUser).at(0).props().isCurrentUser).toBe(true);
    expect(wrapper.find(TeamUser).at(2).props().isCurrentUser).toBe(false);
  });

  it('interleaves agents with users sorted by name', () => {
    mockState({
      users: [generateUser(1, { firstName: 'Bravo' }), generateUser(2, { firstName: 'Delta' })],
      agents: [buildAgent({ id: 10, name: 'Alpha' }), buildAgent({ id: 11, name: 'Charlie' })],
    });

    const wrapper = renderUsers();

    const renderedOrder = wrapper
      .find('.cards')
      .children()
      .map((child) => {
        if (child.is(TeamUser)) {
          return `user:${child.prop('user').id}`;
        }

        return `agent:${child.find(TeamAgent).prop('agent').id}`;
      });

    expect(renderedOrder).toEqual(['agent:10', 'user:1', 'agent:11', 'user:2']);
  });

  it('applies the search query to both users and agents', () => {
    mockState({
      users: [generateUser(1, { firstName: 'Bravo' })],
      agents: [buildAgent({ id: 10, name: 'Charlie' })],
    });

    const wrapper = renderUsers();
    wrapper.find('InputField').simulate('change', { currentTarget: { value: 'charlie' } });
    wrapper.update();

    expect(wrapper.find(TeamUser)).toHaveLength(0);
    expect(wrapper.find(TeamAgent)).toHaveLength(1);
    expect(wrapper.find(TeamAgent).prop('agent').id).toBe(10);
  });

  it('shows skeletons while agents are loading', () => {
    mockState({ areAgentsLoading: true });

    const wrapper = renderUsers();

    expect(wrapper.find(TeamUserSkeleton)).toHaveLength(3);
    expect(wrapper.find(TeamUser)).toHaveLength(0);
  });

  it('loads users, invites, agents and providers on mount', () => {
    mockState({ agents: [buildAgent()] });

    render(<Users userListSorting={EUserListSorting.NameAsc} />);

    expect(mockDispatch).toHaveBeenCalledWith(teamFetchStarted({}));
    expect(mockDispatch).toHaveBeenCalledWith(loadInvitesUsers());
    expect(mockDispatch).toHaveBeenCalledWith(loadAIAgents());
    expect(mockDispatch).toHaveBeenCalledWith(loadAIProviders());
  });
});

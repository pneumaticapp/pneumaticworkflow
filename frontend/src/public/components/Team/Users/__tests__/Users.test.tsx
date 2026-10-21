import * as React from 'react';
import { shallow } from 'enzyme';
import { fireEvent, render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Users } from '../Users';
import { TeamUserCard } from '../TeamUserCard';
import { TeamAgent } from '../TeamAgent';
import { TeamUserSkeleton } from '../../TeamUserSkeleton';
import { generateUser, mockLastNameUsers } from '../../../../__stubs__/users';
import { EUserListSorting } from '../../../../types/user';
import { EAIVendor } from '../../../../api/ai/types';
import type { IAIAgent, IAIProvider } from '../../../../api/ai/types';
import type { TUserListItem } from '../../../../types/user';

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
  TeamUser: ({ user }: { user: TUserListItem }) => {
    const [expanded, setExpanded] = React.useState(false);
    return (
      <button type="button" data-testid={`team-user-card-${user.id}`} onClick={() => setExpanded(true)}>
        {expanded ? 'Expanded' : 'Collapsed'}
      </button>
    );
  },
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

  it('interleaves agents with users sorted by name', () => {
    mockState({
      users: [generateUser(1, { firstName: 'Bravo' }), generateUser(2, { firstName: 'Delta' })],
      agents: [buildAgent({ id: 10, name: 'Alpha' }), buildAgent({ id: 11, name: 'Charlie' })],
    });

    const wrapper = renderUsers();

    const listItems = wrapper.find('ul.cards__list').children('li');
    const renderedOrder = listItems.map((item) => {
      const userCard = item.find(TeamUserCard);
      if (userCard.exists()) {
        return `user:${userCard.prop('user').id}`;
      }

      return `agent:${item.find(TeamAgent).prop('agent').id}`;
    });

    expect(renderedOrder).toEqual(['agent:10', 'user:1', 'agent:11', 'user:2']);
  });

  it('preserves user card state when sorting a user and an agent with the same id', () => {
    mockState({
      users: [generateUser(10, { firstName: 'Bravo' })],
      agents: [buildAgent({ id: 10, name: 'Alpha' })],
    });

    const { rerender } = render(<Users userListSorting={EUserListSorting.NameDesc} />);
    fireEvent.click(screen.getByTestId('team-user-card-10'));
    rerender(<Users userListSorting={EUserListSorting.NameAsc} />);

    expect(screen.getByTestId('team-user-card-10')).toHaveTextContent('Expanded');
    expect(screen.getAllByTestId('team-agent-card')).toHaveLength(1);
  });

  it('applies the search query to both users and agents', () => {
    mockState({
      users: [generateUser(1, { firstName: 'Bravo' })],
      agents: [buildAgent({ id: 10, name: 'Charlie' })],
    });

    const wrapper = renderUsers();
    wrapper.find('InputField').simulate('change', { currentTarget: { value: 'charlie' } });
    wrapper.update();

    expect(wrapper.find(TeamUserCard)).toHaveLength(0);
    expect(wrapper.find(TeamAgent)).toHaveLength(1);
    expect(wrapper.find(TeamAgent).prop('agent').id).toBe(10);
  });

  it('shows skeletons while agents are loading', () => {
    mockState({ areAgentsLoading: true });

    const wrapper = renderUsers();

    expect(wrapper.find(TeamUserSkeleton)).toHaveLength(3);
    expect(wrapper.find(TeamUserCard)).toHaveLength(0);
  });
});

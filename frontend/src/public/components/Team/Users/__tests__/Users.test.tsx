import * as React from 'react';
import { shallow } from 'enzyme';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Users } from '../Users';
import { TeamUserCard } from '../TeamUserCard';
import { TeamUserSkeleton } from '../../TeamUserSkeleton';
import { generateUser, mockLastNameUsers } from '../../../../__stubs__/users';
import { EUserListSorting } from '../../../../types/user';
import { loadAIAgents } from '../../../../redux/ai/slice';
import type { IAIAgent } from '../../../../api/ai/types';
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
  isUsersLoading?: boolean;
}

describe('Users', () => {
  const mockDispatch = jest.fn();

  const mockState = ({ users = mockLastNameUsers, agents = [], isUsersLoading = false }: IMockStateParams = {}) => {
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
          agents: { isLoading: false, list: agents },
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

  it('lists only people and does not load AI agents', () => {
    mockState({
      users: [generateUser(1, { firstName: 'Bravo' }), generateUser(2, { firstName: 'Delta' })],
      agents: [buildAgent({ id: 10, name: 'Alpha' })],
    });

    render(<Users userListSorting={EUserListSorting.NameAsc} />);

    expect(screen.getAllByTestId(/^team-user-card-/)).toHaveLength(2);
    expect(screen.queryByText('Alpha')).not.toBeInTheDocument();
    expect(mockDispatch).not.toHaveBeenCalledWith(loadAIAgents());
  });

  it('applies the search query to users', () => {
    mockState({
      users: [generateUser(1, { firstName: 'Bravo' }), generateUser(2, { firstName: 'Charlie' })],
    });

    const wrapper = renderUsers();
    wrapper.find('InputField').simulate('change', { currentTarget: { value: 'charlie' } });
    wrapper.update();

    expect(wrapper.find(TeamUserCard)).toHaveLength(1);
    expect(wrapper.find(TeamUserCard).prop('user').id).toBe(2);
  });

  it('shows skeletons while users are loading', () => {
    mockState({ isUsersLoading: true });

    const wrapper = renderUsers();

    expect(wrapper.find(TeamUserSkeleton)).toHaveLength(3);
    expect(wrapper.find(TeamUserCard)).toHaveLength(0);
  });
});

import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { Users } from '../Users';
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

jest.mock('../../CreatePerformerModal', () => ({
  CreatePerformerModal: () => null,
}));

jest.mock('../VacationSettingsModal', () => ({
  VacationSettingsModal: () => null,
}));

jest.mock('../../../PageTitle', () => ({
  PageTitle: () => null,
}));

jest.mock('../TeamUserCard', () => ({
  TeamUserCard: ({ user }: { user: TUserListItem }) => {
    const [expanded, setExpanded] = React.useState(false);
    return (
      <button type="button" data-testid={`team-user-card-${user.id}`} onClick={() => setExpanded(true)}>
        {expanded ? 'Expanded' : 'Collapsed'}
      </button>
    );
  },
}));

jest.mock('../../TeamUserSkeleton', () => ({
  TeamUserSkeleton: () => <div data-testid="team-user-skeleton" />,
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
    const state = {
      authUser: {
        id: 0,
        account: { isSubscribed: true, billingPlan: 'premium' },
      },
      accounts: {
        team: { list: users, isLoading: isUsersLoading },
        userListSorting: EUserListSorting.NameAsc,
      },
      ai: {
        agents: { isLoading: false, list: agents },
      },
    };

    (useSelector as jest.Mock).mockImplementation((selector) => selector(state));
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
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

    render(<Users userListSorting={EUserListSorting.NameAsc} />);
    userEvent.type(screen.getByRole('textbox'), 'charlie');

    expect(screen.getAllByTestId(/^team-user-card-/)).toHaveLength(1);
    expect(screen.getByTestId('team-user-card-2')).toBeInTheDocument();
  });

  it('shows skeletons while users are loading', () => {
    mockState({ isUsersLoading: true });

    render(<Users userListSorting={EUserListSorting.NameAsc} />);

    expect(screen.getAllByTestId('team-user-skeleton')).toHaveLength(3);
    expect(screen.queryByTestId(/^team-user-card-/)).not.toBeInTheDocument();
  });
});

import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { Users } from '../Users';
import { IUsersProps } from '../types';
import { mockLastNameUsers } from '../../../../__stubs__/users';
import { EUserListSorting } from '../../../../types/user';

jest.mock('../TeamUser', () => ({
  TeamUser: ({
    user,
    isCurrentUser,
    isSubscribed,
  }: {
    user: { id: number };
    isCurrentUser?: boolean;
    isSubscribed?: boolean;
  }) => (
    <div
      data-testid="team-user"
      data-user-id={user.id}
      data-is-current-user={String(isCurrentUser)}
      data-is-subscribed={String(isSubscribed)}
    />
  ),
}));
jest.mock('../DeleteTeamUserPopup', () => ({ DeleteTeamUserPopupContainer: () => null }));
jest.mock('../AddGuestsBanner', () => ({ AddGuestsBanner: () => null }));
jest.mock('../CreateUserModal', () => ({
  CreateUserModal: ({ isOpen }: { isOpen: boolean }) => (
    <div data-testid="create-user-modal" data-is-open={String(isOpen)} />
  ),
}));
jest.mock('../VacationSettingsModal', () => ({ VacationSettingsModal: () => null }));

describe('Users', () => {
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

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the heading, search, both buttons and cards for all users', () => {
    render(<Users {...mockProps} />);

    expect(screen.getByRole('heading', { name: 'Team' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search user')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Invite Team/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create User/ })).toBeInTheDocument();
    expect(screen.getAllByTestId('team-user')).toHaveLength(mockLastNameUsers.length);
  });

  it('marks the current user via isCurrentUser', () => {
    render(<Users {...mockProps} />);

    const cards = screen.getAllByTestId('team-user');

    expect(cards[0]).toHaveAttribute('data-is-current-user', 'true');
    expect(cards[2]).toHaveAttribute('data-is-current-user', 'false');
  });

  it('keeps the create user modal closed by default', () => {
    render(<Users {...mockProps} />);

    expect(screen.getByTestId('create-user-modal')).toHaveAttribute('data-is-open', 'false');
  });

  it('passes isSubscribed = true to all cards on the free plan', () => {
    render(<Users {...mockProps} />);

    screen.getAllByTestId('team-user').forEach((card) => {
      expect(card).toHaveAttribute('data-is-subscribed', 'true');
    });
  });
});

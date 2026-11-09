import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { TeamUserCard } from '../TeamUserCard';
import { generateUser } from '../../../../__stubs__/users';
import { intlMock } from '../../../../__stubs__/intlMock';
import { EAbsenceStatus, EUserStatus } from '../../../../types/user';
import { loadChangeUserAdmin } from '../../../../redux/accounts/slice';

jest.mock('rc-switch', () => ({ checked, disabled, onChange, 'data-testid': testId }: Record<string, any>) => (
  <input
    type="checkbox"
    data-testid={testId}
    checked={checked}
    disabled={disabled}
    onChange={(event) => onChange(event.target.checked)}
  />
));

jest.mock('../TeamUserRelationsModals', () => ({
  TeamUserRelationsModals: () => null,
}));

describe('TeamUserCard', () => {
  const mockDispatch = jest.fn();
  const t = (id: string) => intlMock.formatMessage({ id });

  const renderCard = (user = generateUser(7), currentUserId = 1) =>
    render(<TeamUserCard user={user} currentUserId={currentUserId} isSubscribed onOpenVacationModal={jest.fn()} />);

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
  });

  it('renders an active user name with id and email', () => {
    renderCard();

    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Stas Boreckiy');
    expect(screen.getByText('ID 7')).toBeInTheDocument();
    expect(screen.getByText(/stas@boreckiy_7\.app/)).toBeInTheDocument();
    expect(screen.queryByText(t('team.card-absent-badge'))).not.toBeInTheDocument();
  });

  it('marks an absent user', () => {
    renderCard(
      generateUser(7, {
        vacation: { absenceStatus: EAbsenceStatus.Vacation } as ReturnType<typeof generateUser>['vacation'],
      }),
    );

    expect(screen.getByText(t('team.card-absent-badge'))).toBeInTheDocument();
  });

  it('renders an invited user by email with the inviter', () => {
    renderCard(
      generateUser(8, {
        status: EUserStatus.Invited,
        invite: { id: '1', byUsername: 'Ada', dateCreated: '2026-10-01T00:00:00Z', invitedBy: 1, invitedFrom: 'email' },
      }),
    );

    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('stas@boreckiy_8.app');
    expect(screen.getByText(/by Ada/)).toBeInTheDocument();
  });

  it('shows the current user badge instead of the controls', () => {
    renderCard(generateUser(7), 7);

    expect(screen.getByText(t('team.card-current-user-badge'))).toBeInTheDocument();
    expect(screen.queryByTestId('team-user-7-toggle')).not.toBeInTheDocument();
  });

  it('toggles the admin role', () => {
    renderCard(generateUser(7, { isAdmin: false }));

    userEvent.click(screen.getByTestId('team-user-7-toggle'));

    expect(mockDispatch).toHaveBeenCalledWith(
      loadChangeUserAdmin({ id: 7, isAdmin: true, email: 'stas@boreckiy_7.app' }),
    );
  });
});

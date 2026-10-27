import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { TeamUserDetails } from '../TeamUserDetails';
import { generateUser } from '../../../../__stubs__/users';
import { EUserStatus } from '../../../../types/user';

describe('TeamUserDetails', () => {
  it('renders an active user name as a heading with id and email', () => {
    render(<TeamUserDetails user={generateUser(7)} />);

    expect(screen.getByRole('heading', { level: 3, name: 'Stas Boreckiy' })).toBeInTheDocument();
    expect(screen.getByText('ID 7')).toBeInTheDocument();
    expect(screen.getByText(/stas@boreckiy_7\.app/)).toBeInTheDocument();
    expect(screen.queryByTestId('absent-badge')).not.toBeInTheDocument();
  });

  it('renders an invited user by email with the inviter', () => {
    render(
      <TeamUserDetails
        user={generateUser(8, {
          status: EUserStatus.Invited,
          invite: {
            id: '1',
            byUsername: 'Ada',
            dateCreated: '2026-10-01T00:00:00Z',
            invitedBy: 1,
            invitedFrom: 'email',
          },
        })}
      />,
    );

    expect(screen.getByRole('heading', { level: 3, name: 'stas@boreckiy_8.app' })).toBeInTheDocument();
    expect(screen.getByText(/by Ada/)).toBeInTheDocument();
  });

  it('renders nothing for other statuses', () => {
    const { container } = render(<TeamUserDetails user={generateUser(9, { status: EUserStatus.Inactive })} />);

    expect(container).toBeEmptyDOMElement();
  });
});

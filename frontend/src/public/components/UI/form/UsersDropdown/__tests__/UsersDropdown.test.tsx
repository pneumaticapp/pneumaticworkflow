import React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../../../lang/locales/en_US';
import { EUserStatus } from '../../../../../types/user';
import { EOptionTypes, UsersDropdownComponent } from '../UsersDropdown';

jest.mock('../../..', () => ({
  Avatar: () => null,
  Checkbox: ({ title }: { title: React.ReactNode }) => <span>{title}</span>,
  DropdownList: ({ options, formatOptionLabel }: any) => (
    <div>
      {options.map((option: any) => (
        <div key={option.value}>
          {formatOptionLabel(option, { context: 'menu', selectValue: [] })}
        </div>
      ))}
    </div>
  ),
}));

describe('UsersDropdownComponent', () => {
  it('shows invited users without the status suffix', () => {
    const email = 'very-long-invited-user-email@example.com';
    const invitedUser = {
      id: 1,
      email,
      firstName: '',
      lastName: '',
      phone: '',
      photo: '',
      status: EUserStatus.Invited,
      type: 'user' as const,
    };

    render(
      <IntlProvider locale="en" messages={enMessages}>
        <UsersDropdownComponent
          options={[
            {
              ...invitedUser,
              optionType: EOptionTypes.User,
              label: `${email} (invited user)`,
              value: 'user-1',
            },
          ]}
          users={[invitedUser]}
          inviteLabel="Invite team member"
          isTeamInvitesModalOpen={false}
          recentInvitedUsers={[]}
          isAdmin={false}
          onChange={jest.fn()}
          onClickInvite={jest.fn()}
          openTeamInvitesPopup={jest.fn()}
        />
      </IntlProvider>,
    );

    expect(screen.getByText(email)).toBeInTheDocument();
    expect(screen.queryByText(/invited user/i)).not.toBeInTheDocument();
  });
});

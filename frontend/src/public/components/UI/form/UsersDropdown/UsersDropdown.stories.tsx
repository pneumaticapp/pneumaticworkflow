import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { EUserStatus, TUserListItem } from '../../../../types/user';
import { UsersDropdownComponent } from './UsersDropdown';
import { EOptionTypes, TUsersDropdownOption } from './types';

const noOp = () => undefined;

const USERS: TUserListItem[] = [
  {
    id: 1,
    email: 'maya.chen@example.com',
    firstName: 'Maya',
    lastName: 'Chen',
    phone: '',
    photo: '',
    type: 'user',
    status: EUserStatus.Active,
  },
  {
    id: 2,
    email: 'david.okafor@example.com',
    firstName: 'David',
    lastName: 'Okafor',
    phone: '',
    photo: '',
    type: 'user',
    status: EUserStatus.Active,
  },
] as TUserListItem[];

const USER_OPTIONS: TUsersDropdownOption[] = USERS.map((user) => ({
  id: user.id,
  label: `${user.firstName} ${user.lastName}`,
  value: `${EOptionTypes.User}-${user.id}`,
  optionType: EOptionTypes.User,
}));

const meta = {
  title: 'UI/Dropdowns/UsersDropdown',
  component: UsersDropdownComponent,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'User and group picker. A preset over `DropdownList` that adds avatars, checkboxes and the '
          + '"Invite team member" / "All users" actions.',
      },
    },
  },
  argTypes: {
    isMulti: { control: 'boolean' },
    isAdmin: { control: 'boolean' },
    controlSize: { control: 'inline-radio', options: ['lg', 'sm'] },
    isDisabled: { control: 'boolean' },
  },
  args: {
    options: USER_OPTIONS,
    users: USERS,
    inviteLabel: 'Invite team member',
    placeholder: 'Search',
    isTeamInvitesModalOpen: false,
    recentInvitedUsers: [],
    isAdmin: true,
    isMulti: false,
    controlSize: 'lg',
    onChange: noOp,
    onClickInvite: noOp,
    openTeamInvitesPopup: noOp,
  },
} satisfies Meta<typeof UsersDropdownComponent<TUsersDropdownOption>>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithLabel: Story = {
  args: { label: 'Substitutes', isRequired: true },
};

export const WithError: Story = {
  args: { label: 'Substitutes', errorMessage: 'Please select at least one substitute' },
};

function MultiStory({ controlSize, title }: { controlSize: 'lg' | 'sm'; title?: string }) {
  const [selected, setSelected] = useState<TUsersDropdownOption[]>([]);
  const toggle = (option: TUsersDropdownOption) => setSelected((current) => (
    current.some(({ id }) => id === option.id)
      ? current.filter(({ id }) => id !== option.id)
      : [...current, option]
  ));

  return (
    <UsersDropdownComponent
      isMulti
      controlSize={controlSize}
      title={title}
      options={USER_OPTIONS}
      users={USERS}
      value={selected}
      placeholder="Search"
      inviteLabel="Invite team member"
      isTeamInvitesModalOpen={false}
      recentInvitedUsers={[]}
      isAdmin
      onChange={toggle}
      onChangeSelected={toggle}
      onClickInvite={noOp}
      openTeamInvitesPopup={noOp}
      onClickAllUsers={(selectAll: boolean) => setSelected(selectAll ? USER_OPTIONS : [])}
    />
  );
}

export const Multiple: Story = { render: () => <MultiStory controlSize="lg" /> };

/** The "Add performer" control from the task card. */
export const AddPerformer: Story = {
  render: () => <MultiStory controlSize="sm" title="Add performer" />,
};

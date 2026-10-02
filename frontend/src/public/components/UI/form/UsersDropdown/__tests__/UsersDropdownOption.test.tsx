import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import optionStyles from '../../../DropdownList/DropdownOption.css';
import { UsersDropdownOption } from '../UsersDropdownOption';
import { EOptionTypes, TUsersDropdownOption } from '../types';

const INVITE_LABEL = 'Invite team member';
const inviteOption: TUsersDropdownOption = {
  id: 0,
  label: INVITE_LABEL,
  optionType: EOptionTypes.InviteUsers,
  value: EOptionTypes.InviteUsers,
};
const allUsersOption: TUsersDropdownOption = {
  id: -1,
  label: 'All Users',
  optionType: EOptionTypes.AllUsers,
  value: EOptionTypes.AllUsers,
};

describe('UsersDropdownOption', () => {
  it('composes the universal option for the task-specific invite action', () => {
    render(
      <UsersDropdownOption
        option={inviteOption}
        formatOptionLabelMeta={{ context: 'menu', inputValue: '', selectValue: [] }}
        users={[]}
        isSelectAll={false}
        isIndeterminate={false}
        hasValue={false}
        showAllUsers={false}
      />,
    );

    expect(screen.getByText(INVITE_LABEL)).toHaveClass(optionStyles['dropdown-option']);
  });

  it('does not toggle the All Users indicator independently', () => {
    render(
      <UsersDropdownOption
        option={allUsersOption}
        formatOptionLabelMeta={{ context: 'menu', inputValue: '', selectValue: [] }}
        users={[]}
        isSelectAll={false}
        isIndeterminate={false}
        hasValue={false}
        showAllUsers
      />,
    );

    const checkbox = screen.getByRole('checkbox', { name: 'All Users' });
    expect(checkbox).toHaveAttribute('readonly');

    fireEvent.click(checkbox);

    expect(checkbox).not.toBeChecked();
  });
});

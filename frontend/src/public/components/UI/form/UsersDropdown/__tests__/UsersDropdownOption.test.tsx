import React from 'react';
import { render, screen } from '@testing-library/react';

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
});

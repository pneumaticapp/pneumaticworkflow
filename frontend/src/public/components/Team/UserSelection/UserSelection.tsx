import React from 'react';
import { useSelector } from 'react-redux';

import { trackInviteTeamInPage } from '../../../utils/analytics';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { EOptionTypes, UsersDropdown } from '../../UI/form/UsersDropdown';
import { getUsers } from '../../../redux/selectors/user';

export interface IUserSelection {
  selectedUsers: number[];
  uniqKey?: number;
  onChange: (value: any) => void;
  onChangeSelected: (value: any) => void;
  onClickAllUsers(value: boolean, users: number[]): void;
}

export function UserSelection({ selectedUsers, onChange, onChangeSelected, onClickAllUsers }: IUserSelection) {
  const users: ReturnType<typeof getUsers> = getNotDeletedUsers(useSelector(getUsers));
  
  const selectionsDropdownOption = users.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });
  const selectedValue = selectionsDropdownOption.filter((item: any) => selectedUsers.find((id: any) => id === item.id));

  return (
    <UsersDropdown
      placeholder="Search"
      controlSize="sm"
      value={selectedValue}
      staticMenu
      isMulti
      options={selectionsDropdownOption}
      onChangeSelected={onChangeSelected}
      onChange={(option) => {
        onChange(option);
      }}
      inviteLabel="Invite member"
      onClickInvite={() => trackInviteTeamInPage('From groups')}
      onClickAllUsers={(isSelectAll) => {
        onClickAllUsers(isSelectAll, isSelectAll ? [...users.map((user) => user.id)] : []);
      }}
      menuIsOpen
      closeMenuOnSelect={false}
    />
  );
}
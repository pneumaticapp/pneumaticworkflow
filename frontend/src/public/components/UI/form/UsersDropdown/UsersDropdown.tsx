import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { ActionMeta, FormatOptionLabelMeta } from 'react-select';

import { DropdownList } from '../..';
import { UsersDropdownOption } from './UsersDropdownOption';
import { EOptionTypes, IUsersDropdownProps, TUsersDropdownOption } from './types';

export { EOptionTypes } from './types';
export type { IUsersDropdownProps, TUsersDropdownOption } from './types';

export function UsersDropdownComponent<TOption extends TUsersDropdownOption>({
  options,
  users,
  className,
  inviteLabel,
  isTeamInvitesModalOpen,
  recentInvitedUsers,
  isAdmin,
  onChange,
  formatOptionLabel,
  onChangeSelected,
  onClickInvite,
  onUsersInvited,
  openTeamInvitesPopup,
  isMulti,
  onClickAllUsers,
  value,
  errorMessage,
  isRequired,
  ...restProps
}: IUsersDropdownProps<TOption>) {
  const { formatMessage } = useIntl();
  const [isInvitingUsers, setIsInvitingUsers] = useState(false);
  const isSelectAll = value?.length === options.length;
  const isIndeterminate = value?.length && value.length !== options.length;

  const userInviteOption = {
    optionType: EOptionTypes.InviteUsers,
    value: EOptionTypes.InviteUsers,
    label: formatMessage({ id: 'template.invite-team-member' }),
    onClick: () => {
      onClickInvite();
      openTeamInvitesPopup();
      setIsInvitingUsers(true);
    },
  };

  const allUsersOption = {
    optionType: EOptionTypes.AllUsers,
    value: EOptionTypes.AllUsers,
    label: formatMessage({ id: 'template.all-users' }),
    onClick: () => {
      if (onClickAllUsers) onClickAllUsers(!isSelectAll);
    },
  };

  const normalizedOptions = [isAdmin && userInviteOption, onClickAllUsers && allUsersOption, ...(options || [])].filter(
    Boolean,
  ) as TOption[];

  useEffect(() => {
    if (!isTeamInvitesModalOpen) setIsInvitingUsers(false);
  }, [isTeamInvitesModalOpen]);

  useEffect(() => {
    if (isInvitingUsers) onUsersInvited?.(recentInvitedUsers);
  }, [recentInvitedUsers]);

  const handleOnChange = (newValue: TOption, { action, option }: ActionMeta<TOption>) => {
    if (action === 'pop-value') return;
    if (isMulti && option) {
      if (onChangeSelected && action === 'deselect-option') {
        onChangeSelected(option);
        return;
      }
      onChange(option);
      return;
    }

    onChange(newValue);
  };

  const handleFormatOptionLabel = (
    option: TOption,
    formatOptionLabelMeta: FormatOptionLabelMeta<TOption>,
  ) => {
    const isBuiltInOption = [EOptionTypes.InviteUsers, EOptionTypes.AllUsers].includes(option.optionType);
    const customLabel = !isBuiltInOption && formatOptionLabel
      ? formatOptionLabel(option, formatOptionLabelMeta)
      : undefined;

    return (
      <UsersDropdownOption
        option={option}
        formatOptionLabelMeta={formatOptionLabelMeta}
        users={users}
        isMulti={isMulti}
        isSelectAll={Boolean(isSelectAll)}
        isIndeterminate={Boolean(isIndeterminate)}
        hasValue={Boolean(value?.length)}
        showAllUsers={Boolean(onClickAllUsers)}
        customLabel={customLabel}
      />
    );
  };

  return (
    <DropdownList
      isMulti={isMulti}
      isSearchable
      options={normalizedOptions}
      onChange={handleOnChange}
      formatOptionLabel={handleFormatOptionLabel}
      className={className}
      value={value}
      errorMessage={errorMessage}
      isRequired={isRequired}
      {...restProps}
    />
  );
}

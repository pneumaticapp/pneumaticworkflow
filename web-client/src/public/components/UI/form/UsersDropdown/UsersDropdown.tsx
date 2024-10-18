import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { ActionMeta, FormatOptionLabelMeta } from 'react-select';

import { TDropdownOptionBase, IDropdownListProps, DropdownList, Checkbox, Avatar, TAvatarUser } from "../..";
import { IUnsavedUser, TUserListItem } from '../../../../types/user';
import { BoldPlusIcon } from '../../../icons';
import { ETaskPerformerType } from '../../../../types/template';
import { getUserById } from '../../../UserData/utils/getUserById';

import styles from './UsersDropdown.css';

export enum EOptionTypes {
  User = ETaskPerformerType.User,
  Starter = ETaskPerformerType.WorkflowStarter,
  Field = ETaskPerformerType.OutputUser,
  InviteUsers = 'invite-users',
}

export type TUsersDropdownOption = Pick<IUnsavedUser, 'firstName' | 'lastName'> &
  TDropdownOptionBase & {
    id: number;
    optionType: EOptionTypes;
  };

export interface IUsersDropdownProps<TOption extends TUsersDropdownOption> extends IDropdownListProps<TOption> {
  inviteLabel: string;
  users: TUserListItem[];
  isTeamInvitesModalOpen: boolean;
  recentInvitedUsers: TUserListItem[];
  isAdmin: boolean;
  onChange: (value: any) => void;
  onChangeSelected?: (value: any) => void;
  openTeamInvitesPopup(): void;
  onUsersInvited?(invitedUsers: any): void;
  onClickInvite(): void;
}

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
  ...restProps
}: IUsersDropdownProps<TOption>) {
  const { formatMessage } = useIntl();
  const [isInvitingUsers, setIsInvitingUsers] = useState(false);

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

  const normalizedOptions = [isAdmin && userInviteOption, ...(options || [])].filter(Boolean) as TOption[];

  useEffect(() => {
    if (!isTeamInvitesModalOpen) setIsInvitingUsers(false);
  }, [isTeamInvitesModalOpen]);

  useEffect(() => {
    if (isInvitingUsers) onUsersInvited?.(recentInvitedUsers);
  }, [recentInvitedUsers]);

  const handleOnChange = (newValue: TOption, { action, option }: ActionMeta<TOption>) => {
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
    option: TUsersDropdownOption,
    formatOptionLabelMeta: FormatOptionLabelMeta<TUsersDropdownOption>,
  ) => {
    if (option.optionType === EOptionTypes.InviteUsers) {
      return (
        <div className={styles['invite-user-option']}>
          <BoldPlusIcon className={styles['invite-user-option__icon']} />
          {inviteLabel}
        </div>
      );
    }

    if (formatOptionLabel) return formatOptionLabel(option, formatOptionLabelMeta);

    const isSelected = !!formatOptionLabelMeta.selectValue.find((item: any) => item.value === option.value);

    const renderLabel = () => {
      const currentUser: TUserListItem | TUsersDropdownOption | null = getUserById(users, Number(option.id));

      return (
        <div className={styles['user-option__content']} title={option.label}>
          {formatOptionLabelMeta.context === 'menu' && (
            <Avatar
              size="sm"
              user={currentUser as unknown as TAvatarUser}
              containerClassName={styles['user-option__avatar']}
              isEmpty={option.optionType !== EOptionTypes.User}
            />
          )}
          <p>{option.label}</p>
        </div>
      );
    };

    return (
      <div className={styles['user-option']}>
        {isMulti ? <Checkbox title={renderLabel()} checked={isSelected} /> : renderLabel()}
      </div>
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
      {...restProps}
    />
  );
}

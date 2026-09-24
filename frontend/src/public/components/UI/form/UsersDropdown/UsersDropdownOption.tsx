import React from 'react';
import classnames from 'classnames';

import { Avatar, Checkbox, DropdownOption, TAvatarUser } from '../..';
import { BoldPlusIcon } from '../../../icons';
import { EUserStatus, isUserAbsent, TUserListItem } from '../../../../types/user';
import { getUserById } from '../../../UserData/utils/getUserById';
import { isUsersDropdownOptionSelected } from './usersDropdownOptionValue';
import { EOptionTypes, IUsersDropdownOptionProps, TUsersDropdownOption } from './types';

import styles from './UsersDropdown.css';

export function UsersDropdownOption({
  option,
  formatOptionLabelMeta,
  users,
  isMulti,
  isSelectAll,
  isIndeterminate,
  hasValue,
  showAllUsers,
  customLabel,
}: IUsersDropdownOptionProps) {
  if (option.optionType === EOptionTypes.InviteUsers) {
    return (
      <DropdownOption
        className={styles['invite-user-option']}
        label={(
          <>
            <BoldPlusIcon className={styles['invite-user-option__icon']} />
            {option.label}
          </>
        )}
      />
    );
  }

  if (option.optionType === EOptionTypes.AllUsers && showAllUsers) {
    return (
      <DropdownOption
        className={styles['invite-user-option']}
        label={(
          <Checkbox
            readOnly
            onChange={(event) => {
              event.preventDefault();
              event.stopPropagation();
            }}
            title={option.label}
            {...(isSelectAll && { triState: 'checked' })}
            {...(isIndeterminate && { triState: 'indeterminate' })}
            {...(!hasValue && { triState: 'empty' })}
          />
        )}
      />
    );
  }

  if (customLabel !== undefined) {
    return <DropdownOption label={customLabel} />;
  }

  const isSelected = isUsersDropdownOptionSelected(formatOptionLabelMeta.selectValue, option);
  const currentUser: TUserListItem | TUsersDropdownOption | null =
    option.optionType !== EOptionTypes.Group ? getUserById(users, Number(option.id)) : option;
  const isInvited = currentUser?.status === EUserStatus.Invited || option.status === EUserStatus.Invited;
  const displayLabel = isInvited
    ? currentUser?.email || option.email || String(option.label).replace(/\s*\(invited user\)\s*$/i, '')
    : option.label;
  const label = (
    <div className={styles['user-option__content']} title={displayLabel as string}>
      {formatOptionLabelMeta.context === 'menu' && (
        <Avatar
          size="sm"
          user={currentUser as unknown as TAvatarUser}
          containerClassName={styles['user-option__avatar']}
          isEmpty={option.optionType !== EOptionTypes.User && option.optionType !== EOptionTypes.Group}
        />
      )}
      <p className={classnames(styles['user-option__label'], isInvited && styles['user-option__label_invited'])}>
        {displayLabel}
        {isUserAbsent(currentUser as TUserListItem) && (
          <span className={styles['user-option__badge']}>
            {(currentUser as TUserListItem)?.vacation?.absenceStatus === 'sick_leave' ? ' 🏥' : ' ✈️'}
          </span>
        )}
      </p>
    </div>
  );

  return (
    <DropdownOption
      className={styles['user-option']}
      label={isMulti ? (
        <Checkbox
          onChange={(event) => {
            event.preventDefault();
            event.stopPropagation();
          }}
          title={label}
          checked={isSelected}
          containerClassName={styles['user-option__checkbox']}
          labelClassName={styles['user-option__checkbox-label']}
          titleClassName={styles['user-option__checkbox-title']}
        />
      ) : label}
    />
  );
}

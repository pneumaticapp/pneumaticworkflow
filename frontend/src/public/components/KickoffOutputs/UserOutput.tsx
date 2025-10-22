import React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getUsers } from '../../redux/selectors/user';
import { IExtraField } from '../../types/template';
import { getUserFullName } from '../../utils/users';

import styles from './KickoffOutputs.css';
import { IApplicationState } from '../../types/redux';

export function UserOutput({ groupId, userId, name }: IExtraField) {
  const { formatMessage } = useIntl();
  const users: ReturnType<typeof getUsers> = useSelector(getUsers);
  const groups = useSelector((state: IApplicationState) => state.groups.list);

  const defaultValue = formatMessage({ id: 'template.kick-off-form-unfilled-value' });
  let displayValue = '';

  if (groupId) {
    const selectedGroup = groups.find((group) => group.id === groupId);
    displayValue = selectedGroup ? selectedGroup.name : defaultValue;
  } else {
    const selectedUser = users.find((user) => user.id === userId);
    displayValue = selectedUser ? getUserFullName(selectedUser) : defaultValue;
  }

  return (
    <p className={styles['output']}>
      <span className={styles['output__name']}>{name}</span>
      <span className={styles['output__text']}>{displayValue}</span>
    </p>
  );
}

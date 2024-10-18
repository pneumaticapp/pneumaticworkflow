/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getUsers } from '../../redux/selectors/user';
import { IExtraField } from '../../types/template';
import { getUserFullName } from '../../utils/users';

import styles from './KickoffOutputs.css';

export function UserOutput({ name, value }: IExtraField) {
  const { formatMessage } = useIntl();
  const users: ReturnType<typeof getUsers> = useSelector(getUsers);

  const renderSelections = () => {
    const defaultValue = formatMessage({ id: 'template.kick-off-form-unfilled-value' });

    const selectedUser = users.find(user => user.id === Number(value));
    const userName = getUserFullName(selectedUser);
    const displayValue = selectedUser ? userName : defaultValue;

    return (
      <span className={styles['output__text']}>
        {displayValue}
      </span>
    );
  };

  return (
    <p className={styles['output']}>
      <span className={styles['output__name']}>
        {name}
      </span>
      {renderSelections()}
    </p>
  );
}

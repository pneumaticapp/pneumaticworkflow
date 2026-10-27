import * as React from 'react';
import { useIntl } from 'react-intl';

import { EUserStatus, isUserAbsent } from '../../../types/user';
import { Header } from '../../UI';
import { getUserFullName } from '../../../utils/users';
import { getDate } from '../../../utils/strings';
import type { ITeamUserDetailsProps } from './types';

import styles from './Users.css';

export function TeamUserDetails({ user }: ITeamUserDetailsProps) {
  const { formatMessage } = useIntl();
  const { status, email, invite } = user;

  if (status === EUserStatus.Active) {
    return (
      <div>
        <Header size="6" tag="h3" className={styles['card-header']}>
          {getUserFullName(user)}
          {isUserAbsent(user) && (
            <span className={styles['card-absent-badge']} data-testid="absent-badge">
              {formatMessage({ id: 'team.card-absent-badge' })}
            </span>
          )}
        </Header>
        <p className={styles['card-subheader']}>
          <strong>{formatMessage({ id: 'team.user-id' }, { id: user.id })}</strong>{' '}
          {formatMessage({ id: 'team.user-email' }, { email: user.email })}
        </p>
      </div>
    );
  }

  if (status === EUserStatus.Invited) {
    return (
      <div>
        <Header size="6" tag="h3" className={styles['card-header']}>
          {email}
        </Header>
        <p className={styles['card-subheader']}>
          {formatMessage(
            { id: 'team.user-invited' },
            { date: getDate(invite?.dateCreated), username: invite?.byUsername },
          )}
        </p>
      </div>
    );
  }

  return null;
}

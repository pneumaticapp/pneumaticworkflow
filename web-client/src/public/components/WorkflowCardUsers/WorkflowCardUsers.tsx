/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Avatar } from '../UI/Avatar';
import { isArrayWithItems } from '../../utils/helpers';
import { UserData } from '../UserData';

import styles from './WorkflowCardUsers.css';

export interface IWorkflowCardUsersProps {
  users?: number[];
  maxUsers?: number;
}

const MAX_SHOW_USERS = 5;

export function WorkflowCardUsers({ users, maxUsers = MAX_SHOW_USERS }: IWorkflowCardUsersProps) {
  if (!isArrayWithItems(users)) {
    return null;
  }
  const usersLeft = Math.max(users.length - maxUsers, 0);

  return (
    <div className={styles['card-users']}>
      {users.slice(0, maxUsers).map((userId, index) => (
        <UserData userId={userId} key={userId}>
          {user => {
            if (!user) {
              return null;
            }

            return (
              <Avatar
                key={index}
                user={user}
                containerClassName={styles['card-user']}
                showInitials={false}
                withTooltip
                size="sm"
              />
            );
          }}
        </UserData>
      ))}
      {Boolean(usersLeft) && <span className={styles['card-users__more']}>+{usersLeft}</span>}
    </div>
  );
}

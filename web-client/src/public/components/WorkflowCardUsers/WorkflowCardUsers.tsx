import * as React from 'react';
import { Avatar } from '../UI/Avatar';
import { isArrayWithItems } from '../../utils/helpers';
import { RawPerformer } from '../../types/template';
import UserDataWithGroup from '../UserDataWithGroup';

import styles from './WorkflowCardUsers.css';

export interface IWorkflowCardUsersProps {
  users?: RawPerformer[];
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
      {users.slice(0, maxUsers).map(({ type, sourceId }) => {
        return <UserDataWithGroup idItem={sourceId} type={type}>
          {(user) => {
            return (
              <Avatar
                key={user?.id}
                user={user}
                containerClassName={styles['card-user']}
                showInitials={false}
                withTooltip
                size="sm"
              />
            );
          }}
        </UserDataWithGroup>;
      })}
      {Boolean(usersLeft) && <span className={styles['card-users__more']}>+{usersLeft}</span>}
    </div>
  );
}

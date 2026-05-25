import React from 'react';
import { Avatar } from '../UI/Avatar';
import { isArrayWithItems } from '../../utils/helpers';
import { ETemplateOwnerType, RawPerformer } from '../../types/template';
import UserDataWithGroup from '../UserDataWithGroup';

import styles from './WorkflowCardUsers.css';

export interface IWorkflowCardUsersProps {
  users?: RawPerformer[];
  maxUsers?: number;
  showAllUsers?: boolean;
  applyFilterPerformer?: (performerIds: number[], groupIds: number[]) => void;
}

const MAX_SHOW_USERS = 5;

export function WorkflowCardUsers({
  users,
  maxUsers = MAX_SHOW_USERS,
  showAllUsers,
  applyFilterPerformer,
}: IWorkflowCardUsersProps) {
  if (!isArrayWithItems(users)) {
    return null;
  }
  const usersLeft = Math.max(users.length - maxUsers, 0);
  const usersToShow = showAllUsers ? users : users.slice(0, maxUsers);

  return (
    <div className={styles['card-users']}>
      {usersToShow.map(({ type, sourceId }) => {
        return (
          <UserDataWithGroup idItem={sourceId} type={type} key={`${type}-${sourceId}`}>
            {(user) => {
              const avatar = (
                <Avatar
                  key={user?.id}
                  user={user}
                  containerClassName={styles['card-user']}
                  showInitials={false}
                  withTooltip
                  size="sm"
                />
              );

              return applyFilterPerformer ? (
                <button
                  type="button"
                  aria-label="apply filter performer"
                  onClick={() =>
                    applyFilterPerformer(
                      type === ETemplateOwnerType.User ? [sourceId] : [],
                      type === ETemplateOwnerType.UserGroup ? [sourceId] : [],
                    )
                  }
                >
                  {avatar}
                </button>
              ) : (
                avatar
              );
            }}
          </UserDataWithGroup>
        );
      })}

      {!showAllUsers && Boolean(usersLeft) && <span className={styles['card-users__more']}>+{usersLeft}</span>}
    </div>
  );
}

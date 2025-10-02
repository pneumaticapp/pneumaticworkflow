import React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { Avatar } from '../../../../UI/Avatar';
import { RemovePerformerIcon } from '../../../../icons';
import { UserData } from '../../../../UserData';

import styles from './WorkflowLogRemovedPerformer.css';

export interface IWorkflowLogRemovedPerformerProps
  extends Pick<IWorkflowLogItem, 'created' | 'userId' | 'targetUserId'> {}

export function WorkflowLogRemovedPerformer({ userId, created, targetUserId }: IWorkflowLogRemovedPerformerProps) {
  const { formatMessage } = useIntl();

  return (
    <UserData userId={userId}>
      {(user) => {
        if (!user) {
          return null;
        }

        return (
          <div className={styles['container']}>
            <div className={styles['avatar']}>
              <Avatar user={user} size="lg" sizeMobile="sm" />
            </div>
            <div className={styles['body']}>
              <p className={styles['title']}>
                <span className={styles['title__text']}>{getUserFullName(user)}</span>
                <span className={styles['title__icon']}>
                  <RemovePerformerIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              {targetUserId && (
                <div className={styles['text']}>
                  {formatMessage({ id: 'task.log-removed-performer' })}
                  <UserData userId={targetUserId}>
                    {(userData) => {
                      if (!userData) {
                        return null;
                      }

                      return (
                        <span className={styles['username']}>{getUserFullName(userData, { withAtSign: true })}</span>
                      );
                    }}
                  </UserData>
                </div>
              )}
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

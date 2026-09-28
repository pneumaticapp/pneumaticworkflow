import * as React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { Avatar } from '../../../../UI/Avatar';
import { AddPerformerIcon } from '../../../../icons';
import { UserData } from '../../../../UserData';

import styles from './WorkflowLogAddedPerformer.css';

export interface IWorkflowLogAddedPerformerProps extends Pick<IWorkflowLogItem, 'created' | 'targetUserId'> {}

export function WorkflowLogAddedPerformer({ created, targetUserId }: IWorkflowLogAddedPerformerProps) {
  const { formatMessage } = useIntl();

  return (
    <div className={styles['container']}>
      <div className={styles['avatar']}>
        <Avatar size="lg" sizeMobile="sm" isSystemAvatar />
      </div>
      <div className={styles['body']}>
        <p className={styles['title']}>
          <span className={styles['title__text']}>{formatMessage({ id: 'general.pneumatic' })}</span>
          <span className={styles['title__icon']}>
            <AddPerformerIcon />
          </span>
          <span className={styles['title__date']}>
            <DateFormat date={created} />
          </span>
        </p>

        {targetUserId && (
          <div className={styles['text']}>
            {formatMessage({ id: 'task.log-added-performer' })}
            <UserData userId={targetUserId}>
              {(user) => {
                if (!user) {
                  return null;
                }

                return <span className={styles['username']}>{getUserFullName(user, { withAtSign: true })}</span>;
              }}
            </UserData>
          </div>
        )}
      </div>
    </div>
  );
}

import * as React from 'react';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { AlarmCrossedIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { UserData } from '../../../../UserData';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import styles from './WorkflowLogWorkflowResumed.css';

export type TWorkflowLogWorkflowResumedProps = Pick<IWorkflowLogItem, 'userId' | 'created'>;

export function WorkflowLogWorkflowResumed({ userId, created }: TWorkflowLogWorkflowResumedProps) {
  const { formatMessage } = useIntl();

  return (
    <UserData userId={userId}>
      {(userData) => {
        if (!userData) {
          return null;
        }

        return (
          <div className={styles['container']}>
            <div className={styles['avatar']}>
              <Avatar user={userData} size="lg" sizeMobile="sm" />
            </div>
            <div className={styles['body']}>
              <p className={styles['title']}>
                <span className={styles['title__text']}>{getUserFullName(userData)}</span>
                <span className={styles['title__icon']}>
                  <AlarmCrossedIcon fill="#4CAF50" />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              <div className={styles['text']}>{formatMessage({ id: 'workflows.event-resumed' })}</div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

import * as React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { Avatar } from '../../../../UI/Avatar';
import { ReturnTaskInfoIcon } from '../../../../icons';
import { UserData } from '../../../../UserData';

import styles from './WorkflowLogProcessReturn.css';

export interface IWorkflowLogProcessReturnProps extends Pick<IWorkflowLogItem, 'created' | 'userId'> {}

export function WorkflowLogProcessReturn({ userId, created }: IWorkflowLogProcessReturnProps) {
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
                  <ReturnTaskInfoIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              <div className={styles['text']}>{formatMessage({ id: 'task.log-returned' })}</div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

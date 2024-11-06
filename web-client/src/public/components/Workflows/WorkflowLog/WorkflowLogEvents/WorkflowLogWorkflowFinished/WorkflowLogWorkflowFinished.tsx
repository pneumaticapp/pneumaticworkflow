import React from 'react';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { WorkflowEndedIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { UserData } from '../../../../UserData';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import styles from './WorkflowLogWorkflowFinished.css';

export type TWorkflowLogWorkflowFinishedProps = Pick<IWorkflowLogItem, 'userId' | 'created'>;

export function WorkflowLogWorkflowFinished({ userId, created }: TWorkflowLogWorkflowFinishedProps) {
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
                  <WorkflowEndedIcon />
                </span>
                <span className={styles['title__date']}><DateFormat date={created} /></span>
              </p>
              <div className={styles['text']}>{formatMessage({ id: 'workflows.log-workflow-ended' })}</div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

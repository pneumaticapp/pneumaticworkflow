import * as React from 'react';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { UrgentColorIcon, NotUrgentIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { UserData } from '../../../../UserData';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import styles from './WorkflowUrgent.css';

export type TWorkflowUrgentProps = Pick<IWorkflowLogItem, 'userId' | 'created'>;

export interface IWorkflowUrgentProps extends TWorkflowUrgentProps {
  isNotUrgent?: boolean;
}

export function WorkflowUrgent({ userId, created, isNotUrgent = false }: IWorkflowUrgentProps) {
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
                  {isNotUrgent ? <NotUrgentIcon fill="#B9B9B8" /> : <UrgentColorIcon fill="#F44336" />}
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>
              <div className={styles['text']}>
                {isNotUrgent
                  ? formatMessage({ id: 'workflows.no-longer-urgent' })
                  : formatMessage({ id: 'workflows.marked-urgent' })}
              </div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

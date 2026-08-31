import React from 'react';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { WorkflowEndedIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { UserData } from '../../../../UserData';
import { EWorkflowLogEvent, IWorkflowLogItem } from '../../../../../types/workflow';

import styles from './WorkflowLogWorkflowFinished.css';

export type TWorkflowLogWorkflowFinishedProps = Pick<IWorkflowLogItem, 'userId' | 'created' | 'type'>;

export function WorkflowLogWorkflowFinished({ userId, created, type }: TWorkflowLogWorkflowFinishedProps) {
  const { formatMessage } = useIntl();

  const renderEvent = (title: string, avatar: React.ReactNode) => (
    <div className={styles['container']}>
      <div className={styles['avatar']}>{avatar}</div>
      <div className={styles['body']}>
        <p className={styles['title']}>
          <span className={styles['title__text']}>{title}</span>
          <span className={styles['title__icon']}>
            <WorkflowEndedIcon />
          </span>
          <span className={styles['title__date']}>
            <DateFormat date={created} />
          </span>
        </p>
        <div className={styles['text']}>{formatMessage({ id: 'workflows.log-workflow-ended' })}</div>
      </div>
    </div>
  );

  if (type !== EWorkflowLogEvent.WorkflowComplete) {
    return renderEvent(
      formatMessage({ id: 'general.pneumatic' }),
      <Avatar size="lg" sizeMobile="sm" isSystemAvatar />,
    );
  }

  return (
    <UserData userId={userId}>
      {(user) => {
        if (!user) {
          return null;
        }

        return renderEvent(getUserFullName(user), <Avatar user={user} size="lg" sizeMobile="sm" />);
      }}
    </UserData>
  );
}

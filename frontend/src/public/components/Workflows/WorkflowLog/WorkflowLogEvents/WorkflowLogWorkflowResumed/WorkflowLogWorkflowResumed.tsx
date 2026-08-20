import * as React from 'react';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { AlarmCrossedIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import styles from './WorkflowLogWorkflowResumed.css';

export type TWorkflowLogWorkflowResumedProps = Pick<IWorkflowLogItem, 'created'>;

export function WorkflowLogWorkflowResumed({ created }: TWorkflowLogWorkflowResumedProps) {
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
            <AlarmCrossedIcon fill="var(--pneumatic-color-notification3)" />
          </span>
          <span className={styles['title__date']}>
            <DateFormat date={created} />
          </span>
        </p>

        <div className={styles['text']}>{formatMessage({ id: 'workflows.event-resumed' })}</div>
      </div>
    </div>
  );
}

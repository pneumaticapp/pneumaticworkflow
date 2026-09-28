import React from 'react';
import { useIntl } from 'react-intl';

import { useSelector } from 'react-redux';
import { getLanguage } from '../../../../../redux/selectors/user';

import { Avatar } from '../../../../UI/Avatar';
import { AlarmIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { IWorkflowLogItem, IWorkflowDelay } from '../../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../../utils/dateTime';

import styles from './WorkflowLogWorkflowSnoozedManually.css';

export type TWorkflowLogWorkflowSnoozedManuallyProps = Pick<IWorkflowLogItem, 'created'> & {
  delay: IWorkflowDelay;
};

export function WorkflowLogWorkflowSnoozedManually({ created, delay }: TWorkflowLogWorkflowSnoozedManuallyProps) {
  const { formatMessage } = useIntl();
  const locale = useSelector(getLanguage);

  return (
    <div className={styles['container']}>
      <div className={styles['avatar']}>
        <Avatar size="lg" sizeMobile="sm" isSystemAvatar />
      </div>
      <div className={styles['body']}>
        <p className={styles['title']}>
          <span className={styles['title__text']}>{formatMessage({ id: 'general.pneumatic' })}</span>
          <span className={styles['title__icon']}>
            <AlarmIcon fill="var(--pneumatic-color-notification1)" />
          </span>
          <span className={styles['title__date']}>
            <DateFormat date={created} />
          </span>
        </p>

        <div className={styles['text']}>
          {formatMessage({ id: 'workflows.event-snoozed-until' }, { date: getSnoozedUntilDate(delay, locale) })}
        </div>
      </div>
    </div>
  );
}

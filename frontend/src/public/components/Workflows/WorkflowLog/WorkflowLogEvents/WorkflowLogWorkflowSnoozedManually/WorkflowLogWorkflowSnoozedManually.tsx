import React from 'react';
import { useIntl } from 'react-intl';

import { useSelector } from "react-redux";
import { getLanguage } from '../../../../../redux/selectors/user';

import { Avatar } from '../../../../UI/Avatar';
import { AlarmIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { UserData } from '../../../../UserData';
import { IWorkflowLogItem, IWorkflowDelay } from '../../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../../utils/dateTime';

import styles from './WorkflowLogWorkflowSnoozedManually.css';

export type TWorkflowLogWorkflowSnoozedManuallyProps = Pick<IWorkflowLogItem, 'userId' | 'created'> & {
  delay: IWorkflowDelay;
};

export function WorkflowLogWorkflowSnoozedManually({
  userId,
  created,
  delay,
}: TWorkflowLogWorkflowSnoozedManuallyProps) {
  const { formatMessage } = useIntl();
  const locate = useSelector(getLanguage)

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
                  <AlarmIcon fill="#F44336" />
                </span>
                <span className={styles['title__date']}><DateFormat date={created} /></span>
              </p>

              <div className={styles['text']}>
                {formatMessage({ id: 'workflows.event-snoozed-until' }, { date: getSnoozedUntilDate(delay, locate)})}
              </div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

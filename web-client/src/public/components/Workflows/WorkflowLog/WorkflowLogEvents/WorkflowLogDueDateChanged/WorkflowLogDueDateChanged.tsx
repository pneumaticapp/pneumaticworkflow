import * as React from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import { getLanguage } from '../../../../../redux/selectors/user';

import { Avatar } from '../../../../UI/Avatar';
import { ClockIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { UserData } from '../../../../UserData';
import { IWorkflowLogItem } from '../../../../../types/workflow';
import { getDueInData } from '../../../../DueIn/utils/getDueInData';

import styles from './WorkflowLogDueDateChanged.css';

export type TWorkflowLogDueDateChangedProps = Pick<IWorkflowLogItem, 'userId' | 'created' | 'task'>;

export function WorkflowLogDueDateChanged({ userId, created, task }: TWorkflowLogDueDateChangedProps) {
  const { formatMessage } = useIntl();
  const locale = useSelector(getLanguage);
  const dueDateData = task ? getDueInData([task.dueDate], undefined, undefined, locale) : null;
  const dueDate = dueDateData ? <DateFormat date={dueDateData.dueDate} /> : null;

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
                  <ClockIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              <div className={styles['text']}>
                {dueDate
                  ? formatMessage({ id: 'workflows.due-date-changed' }, { date: dueDate })
                  : formatMessage({ id: 'workflows.due-date-removed' })}
              </div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

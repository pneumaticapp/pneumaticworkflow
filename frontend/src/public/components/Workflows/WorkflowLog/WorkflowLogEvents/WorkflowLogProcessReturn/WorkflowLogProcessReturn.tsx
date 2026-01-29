import * as React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { Avatar } from '../../../../UI/Avatar';
import { ReturnTaskInfoIcon } from '../../../../icons';
import { UserData } from '../../../../UserData';

import styles from './WorkflowLogProcessReturn.css';
import { RichText } from '../../../../RichText';

export interface IWorkflowLogProcessReturnProps
  extends Pick<IWorkflowLogItem, 'created' | 'userId' | 'text' | 'task'> {}

export function WorkflowLogProcessReturn({ userId, created, text, task }: IWorkflowLogProcessReturnProps) {
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
            <div>
              <p className={styles['title']}>
                <span className={styles['title__text']}>{getUserFullName(user)}</span>
                <span className={styles['title__icon']}>
                  <ReturnTaskInfoIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              <div className={styles['workflow-log-return__status']}>
                {formatMessage({ id: 'task.log-returned' }, { taskName: task?.name })}
              </div>
              <div className={styles['workflow-log-return__message']}>
                <RichText text={text} />
              </div>
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

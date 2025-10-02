import * as React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { Avatar } from '../../../../UI/Avatar';
import { AddPerformerIcon } from '../../../../icons';
import { UserData } from '../../../../UserData';

import styles from './WorkflowLogAddedPerformerGroup.css';
import UserDataWithGroup from '../../../../UserDataWithGroup';
import { ETemplateOwnerType } from '../../../../../types/template';

export interface IWorkflowLogAddedPerformerProps
  extends Pick<IWorkflowLogItem, 'created' | 'userId' | 'targetGroupId'> {}

export function WorkflowLogAddedPerformerGroup({ userId, created, targetGroupId }: IWorkflowLogAddedPerformerProps) {
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
                  <AddPerformerIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              {targetGroupId && (
                <div className={styles['text']}>
                  {formatMessage({ id: 'task.log-added-performer-group' })}
                  <UserDataWithGroup type={ETemplateOwnerType.UserGroup} idItem={targetGroupId}>
                    {(targetUser) => {
                      return <span className={styles['username']}>{targetUser.firstName}</span>;
                    }}
                  </UserDataWithGroup>
                </div>
              )}
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

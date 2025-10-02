import React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { Avatar } from '../../../../UI/Avatar';
import { RemovePerformerIcon } from '../../../../icons';
import { UserData } from '../../../../UserData';

import styles from './WorkflowLogRemovedPerformerGroup.css';
import UserDataWithGroup from '../../../../UserDataWithGroup';
import { ETemplateOwnerType } from '../../../../../types/template';

export interface IWorkflowLogRemovedPerformerProps
  extends Pick<IWorkflowLogItem, 'created' | 'userId' | 'targetGroupId'> {}

export function WorkflowLogRemovedPerformerGroup({ userId, created, targetGroupId }: IWorkflowLogRemovedPerformerProps) {
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
                  <RemovePerformerIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>

              {targetGroupId && (
                <div className={styles['text']}>
                  {formatMessage({ id: 'task.log-removed-performer-group' })}
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

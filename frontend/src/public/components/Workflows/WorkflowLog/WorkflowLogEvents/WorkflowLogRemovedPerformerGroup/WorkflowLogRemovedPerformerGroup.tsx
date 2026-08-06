import React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { Avatar } from '../../../../UI/Avatar';
import { RemovePerformerIcon } from '../../../../icons';

import styles from './WorkflowLogRemovedPerformerGroup.css';
import UserDataWithGroup from '../../../../UserDataWithGroup';
import { ETemplateOwnerType } from '../../../../../types/template';

export interface IWorkflowLogRemovedPerformerProps extends Pick<IWorkflowLogItem, 'created' | 'targetGroupId'> {}

export function WorkflowLogRemovedPerformerGroup({ created, targetGroupId }: IWorkflowLogRemovedPerformerProps) {
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
}

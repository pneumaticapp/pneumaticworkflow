import * as React from 'react';
import { useIntl } from 'react-intl';
import { IWorkflowLogItem } from '../../../../../types/workflow';

import { DateFormat } from '../../../../UI/DateFormat';
import { Avatar } from '../../../../UI/Avatar';
import { AddPerformerIcon } from '../../../../icons';

import styles from './WorkflowLogAddedPerformerGroup.css';
import UserDataWithGroup from '../../../../UserDataWithGroup';
import { ETemplateOwnerType } from '../../../../../types/template';

export interface IWorkflowLogAddedPerformerProps extends Pick<IWorkflowLogItem, 'created' | 'targetGroupId'> {}

export function WorkflowLogAddedPerformerGroup({ created, targetGroupId }: IWorkflowLogAddedPerformerProps) {
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
}

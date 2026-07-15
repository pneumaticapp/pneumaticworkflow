import React from 'react';
import { useIntl } from 'react-intl';

import { ETemplateOwnerType } from '../../types/template';
import { EWorkflowLogEvent } from '../../types/workflow';
import { getUserFullName } from '../../utils/users';
import { UserData } from '../UserData';
import UserDataWithGroup from '../UserDataWithGroup';

import { IPerformerChangeProps } from './types';

import styles from './FeedItem.css';

export function PerformerChange({ targetGroupId, targetUserId, type }: IPerformerChangeProps) {
  const { formatMessage } = useIntl();
  const isGroup =
    type === EWorkflowLogEvent.AddedPerformerGroup || type === EWorkflowLogEvent.RemovedPerformerGroup;

  if (isGroup) {
    if (!targetGroupId) {
      return null;
    }

    const messageId =
      type === EWorkflowLogEvent.AddedPerformerGroup
        ? 'task.log-added-performer-group'
        : 'task.log-removed-performer-group';

    return (
      <div className={styles['changed-performer']}>
        {formatMessage({ id: messageId })}
        <UserDataWithGroup type={ETemplateOwnerType.UserGroup} idItem={targetGroupId}>
          {(group) => <span className={styles['username']}>{group.firstName}</span>}
        </UserDataWithGroup>
      </div>
    );
  }

  if (!targetUserId) {
    return null;
  }

  const messageId =
    type === EWorkflowLogEvent.AddedPerformer ? 'task.log-added-performer' : 'task.log-removed-performer';

  return (
    <div className={styles['changed-performer']}>
      {formatMessage({ id: messageId })}
      <UserData userId={targetUserId}>
        {(user) => {
          if (!user) {
            return null;
          }

          return <span className={styles['username']}>{getUserFullName(user, { withAtSign: true })}</span>;
        }}
      </UserData>
    </div>
  );
}

import React from 'react';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { DoneInfoIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { getUserFullName } from '../../../../../utils/users';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../../../../KickoffOutputs';
import { isArrayWithItems } from '../../../../../utils/helpers';
import { UserData } from '../../../../UserData';
import { IWorkflowLogTaskCompleteProps } from './types';

import styles from './WorkflowLogTaskComplete.css';

export function WorkflowLogTaskComplete({
  userId,
  created,
  currentTask,
  isOnlyAttachmentsShown = false,
}: IWorkflowLogTaskCompleteProps) {
  const { formatMessage } = useIntl();

  const renderOutputValues = () => {
    const outputs = currentTask?.output?.filter(Boolean) || [];

    if (!isArrayWithItems(outputs)) {
      return null;
    }

    return (
      <KickoffOutputs
        containerClassName={styles['outputs-container']}
        viewMode={EKickoffOutputsViewModes.Short}
        outputs={outputs}
        isOnlyAttachmentsShown={isOnlyAttachmentsShown}
      />
    );
  };

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
                  <DoneInfoIcon />
                </span>
                <span className={styles['title__date']}>
                  <DateFormat date={created} />
                </span>
              </p>
              {!isOnlyAttachmentsShown && (
                <div className={styles['text']}>
                  {formatMessage({ id: 'workflows.log-complete' }, { taskName: currentTask?.name })}
                </div>
              )}
              {renderOutputValues()}
            </div>
          </div>
        );
      }}
    </UserData>
  );
}

import * as React from 'react';
import { useIntl } from 'react-intl';

import { WorkflowEndedIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { IWorkflowLogItem } from '../../../../../types/workflow';
import { Avatar } from '../../../../UI';

import styles from './WorkflowLogWorkflowEndedOnCondition.css';

export type IWorkflowLogWorkflowEndedOnConditionProps = Pick<IWorkflowLogItem, 'created'>;

export function WorkflowLogWorkflowEndedOnCondition({ created }: IWorkflowLogWorkflowEndedOnConditionProps) {
  const { formatMessage } = useIntl();

  return (
    <div className={styles['container']}>
      <div className={styles['avatar']}>
        <Avatar
          size="lg"
          sizeMobile="sm"
          isSystemAvatar
        />
      </div>
      <div className={styles['body']}>
        <p className={styles['title']}>
          <span className={styles['title__text']}>
            {formatMessage({ id: 'general.pneumatic' })}
          </span>
          <span className={styles['title__icon']}><WorkflowEndedIcon /></span>
          <span className={styles['title__date']}><DateFormat date={created} /></span>
        </p>
        <div className={styles['text']}>
          {formatMessage({ id: 'workflows.log-workflow-ended-on-condition' })}
        </div>
      </div>
    </div>
  );
}

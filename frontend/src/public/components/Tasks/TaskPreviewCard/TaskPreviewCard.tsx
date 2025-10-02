/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { getDueInData } from '../../DueIn/utils/getDueInData';
import { ETaskListCompletionStatus, ITaskListItem } from '../../../types/tasks';

import styles from './TaskPreviewCard.css';

export interface ITaskPreviewCardProps {
  task: ITaskListItem;
  isActive?: boolean;
  completionStatus: ETaskListCompletionStatus;
  onClick?(): void;
}

export function TaskPreviewCard({ task, isActive = false, completionStatus, onClick }: ITaskPreviewCardProps) {
  const { name, workflowName } = task;

  const renderDueIn = () => {
    const dueInData = getDueInData([task.dueDate], task.dateCompleted);
    if (!dueInData) {
      return null;
    }

    // hide <due in> in completed tasks list
    if (completionStatus === ETaskListCompletionStatus.Completed && !dueInData.isOverdue) {
      return null;
    }

    return (
      <p className={classnames(styles['due-in'], dueInData.isOverdue && styles['due-in_overdue'])}>
        {dueInData.timeLeft}
      </p>
    );
  };

  return (
    <div
      role="button"
      onClick={onClick}
      className={classnames(
        styles['container'],
        completionStatus === ETaskListCompletionStatus.Completed && styles['container_completed'],
        task.isUrgent && styles['container_urgent'],
        isActive && styles['active'],
      )}
    >
      <div className={styles['top']}>
        <p className={styles['task-name']}>{name}</p>
        {renderDueIn()}
      </div>
      <p className={styles['workflow-name']}>{workflowName}</p>
    </div>
  );
}

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import styles from './FeedItem.css';

import { EWorkflowLogEvent } from '../../types/workflow';

import {
  UrgentColorIcon,
  CommentIcon,
  TaskCompleteIcon,
  ProcessStartIcon
} from '../icons';

export const PerformerIcon = ({ type }: { type: EWorkflowLogEvent }) => {
  switch (type) {
    case EWorkflowLogEvent.TaskComplete:
      return (
        <div className={styles.performer_icon}>
          <TaskCompleteIcon size="sm" />
        </div>
      );
    case EWorkflowLogEvent.WorkflowIsUrgent:
      return (
        <div className={styles.performer_icon}>
          <UrgentColorIcon />
        </div>
      );
    case EWorkflowLogEvent.TaskComment:
      return (
        <div className={styles.performer_icon}>
          <CommentIcon fill="#B9B9B8" size="sm" />
        </div>
      );
    case EWorkflowLogEvent.ProcessRun:
      return (
        <div className={styles.performer_icon}>
          <ProcessStartIcon size="sm" />
        </div>
      );
    default:
      return <></>;
  }
};

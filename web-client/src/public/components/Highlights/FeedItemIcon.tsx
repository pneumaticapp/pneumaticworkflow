import * as React from 'react';
import { useIntl } from 'react-intl';
import * as classnames from 'classnames';

import { ECommentType, EWorkflowLogEvent } from '../../types/workflow';
import {
  CommentIcon,
  ProcessCompleteIcon,
  ProcessFinishIcon,
  ProcessStartIcon,
  TaskCompleteIcon,
  TaskReturnIcon,
  NotUrgentIcon,
  UrgentColorIcon,
  AddUserIcon,
  RemoveUserIcon,
  AlarmIcon,
  AlarmCrossedIcon,
  ClockIcon,
} from '../icons';
import { IHighlightsItem } from '../../types/highlights';
import { getDueInData } from '../DueIn/utils/getDueInData';
import { Tooltip } from '../UI';
import { DateFormat } from '../UI/DateFormat';

import styles from './FeedItem.css';
import { reactElementToText } from '../../utils/reactElementToText';

export interface IFeedItemIconProps {
  className?: string;
  commentType?: ECommentType;
  type: EWorkflowLogEvent;
  task: IHighlightsItem['task'];
}

type TFeedIcon = {
  icon: React.ReactNode;
  tooltipMessage: string;
};

const NULL_FEED_ICON: TFeedIcon = {
  icon: null,
  tooltipMessage: '',
};

export function FeedItemIcon({ className, type, task }: IFeedItemIconProps) {
  const { formatMessage } = useIntl();

  const dueDateData = task ? getDueInData([task.dueDate]) : null;
  const dueDate = dueDateData ? <DateFormat date={dueDateData.dueDate} /> : null;

  const commentIconMap: { [key in ECommentType]: TFeedIcon } = {
    [ECommentType.Comment]: {
      icon: <CommentIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-comment' }),
    },
    [ECommentType.Reverted]: {
      icon: <TaskReturnIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-task-returned' }),
    },
    [ECommentType.Finish]: {
      icon: <ProcessCompleteIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-process-finished' }),
    },
  };

  const eventIconMap: { [key in EWorkflowLogEvent]: TFeedIcon } = {
    [EWorkflowLogEvent.WorkflowComplete]: {
      icon: <ProcessCompleteIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-process-completed' }),
    },
    [EWorkflowLogEvent.WorkflowFinished]: {
      icon: <ProcessFinishIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-process-finished' }),
    },
    [EWorkflowLogEvent.TaskComplete]: {
      icon: <TaskCompleteIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-task-completed' }),
    },
    [EWorkflowLogEvent.WorkflowRun]: {
      icon: <ProcessStartIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-process-started' }),
    },
    [EWorkflowLogEvent.WorkflowsReturned]: {
      icon: <TaskReturnIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-workflow-returned' }),
    },
    [EWorkflowLogEvent.TaskRevert]: {
      icon: <TaskReturnIcon className={className} size="sm" />,
      tooltipMessage: formatMessage({ id: 'workflow-highlights.icon-task-returned' }),
    },
    [EWorkflowLogEvent.WorkflowSnoozed]: NULL_FEED_ICON,
    [EWorkflowLogEvent.TaskComment]: NULL_FEED_ICON,
    [EWorkflowLogEvent.TaskStart]: NULL_FEED_ICON,
    [EWorkflowLogEvent.TaskSkipped]: NULL_FEED_ICON,
    [EWorkflowLogEvent.TaskSkippedDueLackAssignedPerformers]: NULL_FEED_ICON,
    [EWorkflowLogEvent.WorkflowEndedOnCondition]: NULL_FEED_ICON,
    [EWorkflowLogEvent.DueDateChanged]: {
      icon: <ClockIcon className={classnames(styles['due-date-changed-icon'], className)} />,
      tooltipMessage: dueDate
        ? formatMessage({ id: 'workflows.due-date-changed' }, { date: reactElementToText(dueDate) })
        : formatMessage({ id: 'workflows.due-date-removed' }),
    },
    [EWorkflowLogEvent.AddedPerformer]: {
      icon: <AddUserIcon className={className} color="#4CAF50" />,
      tooltipMessage: formatMessage({ id: 'workflows.user-added' }),
    },
    [EWorkflowLogEvent.RemovedPerformer]: {
      icon: <RemoveUserIcon className={className} color="#F44336" />,
      tooltipMessage: formatMessage({ id: 'workflows.user-removed' }),
    },
    [EWorkflowLogEvent.WorkflowIsUrgent]: {
      icon: <UrgentColorIcon className={className} />,
      tooltipMessage: formatMessage({ id: 'workflows.marked-urgent' }),
    },
    [EWorkflowLogEvent.WorkflowIsNotUrgent]: {
      icon: <NotUrgentIcon className={className} />,
      tooltipMessage: formatMessage({ id: 'workflows.no-longer-urgent' }),
    },
    [EWorkflowLogEvent.WorkflowSnoozedManually]: {
      icon: <AlarmIcon className={className} fill="#F44336" />,
      tooltipMessage: formatMessage({ id: 'workflows.event-snoozed' }),
    },
    [EWorkflowLogEvent.WorkflowResumed]: {
      icon: <AlarmCrossedIcon className={className} fill="#4CAF50" />,
      tooltipMessage: formatMessage({ id: 'workflows.event-resumed' }),
    },
  };

  const isComment = type === EWorkflowLogEvent.TaskComment;

  const { icon, tooltipMessage: tooltipMessageId } = isComment
    ? commentIconMap[ECommentType.Comment]
    : eventIconMap[type];

  return (
    <Tooltip content={tooltipMessageId}>
      <span>{icon}</span>
    </Tooltip>
  );
}

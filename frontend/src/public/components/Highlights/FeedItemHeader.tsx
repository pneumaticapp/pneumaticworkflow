import React, { useState } from 'react';
import { useIntl } from 'react-intl';

import { EWorkflowLogEvent } from '../../types/workflow';
import { getSnoozedUntilDate } from '../../utils/dateTime';

import { FeedItemComment } from './FeedItemComment';
import { FeedItemOutputs } from './FeedItemOutputs';
import { PerformerChange } from './PerformerChange';
import { IFeedItemHeaderProps } from './types';

export function FeedItemHeader({
  attachments,
  text,
  type,
  workflow: { kickoff },
  task,
  delay,
  targetUserId,
  targetGroupId,
}: IFeedItemHeaderProps) {
  const { formatMessage } = useIntl();
  const [isTextExpanded, setIsTextExpanded] = useState(false);
  const handleExpand = () => setIsTextExpanded(true);

  switch (type) {
    case EWorkflowLogEvent.TaskComplete:
    case EWorkflowLogEvent.WorkflowRun:
    case EWorkflowLogEvent.WorkflowComplete:
    case EWorkflowLogEvent.WorkflowsReturned:
      return (
        <FeedItemOutputs
          kickoff={kickoff}
          isTextExpanded={isTextExpanded}
          onExpand={handleExpand}
          task={task}
          type={type}
        />
      );

    case EWorkflowLogEvent.TaskComment:
    case EWorkflowLogEvent.WorkflowFinished:
    case EWorkflowLogEvent.TaskRevert:
      return (
        <FeedItemComment
          attachments={attachments}
          isTextExpanded={isTextExpanded}
          onExpand={handleExpand}
          task={task}
          text={text}
          type={type}
        />
      );

    case EWorkflowLogEvent.AddedPerformer:
    case EWorkflowLogEvent.RemovedPerformer:
    case EWorkflowLogEvent.AddedPerformerGroup:
    case EWorkflowLogEvent.RemovedPerformerGroup:
      return (
        <PerformerChange
          targetGroupId={targetGroupId}
          targetUserId={targetUserId}
          type={type}
        />
      );

    case EWorkflowLogEvent.WorkflowSnoozedManually:
      return (
        <>{formatMessage({ id: 'workflows.event-snoozed-until' }, { date: getSnoozedUntilDate(delay || null) })}</>
      );

    case EWorkflowLogEvent.WorkflowResumed:
      return <>{formatMessage({ id: 'workflows.event-resumed' })}</>;

    default:
      return null;
  }
}

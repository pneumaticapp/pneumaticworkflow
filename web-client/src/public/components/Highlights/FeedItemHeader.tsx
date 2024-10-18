import React, { useState, useEffect, useRef } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { RichText } from '../RichText';
import { Attachments } from '../Attachments';
import { EWorkflowLogEvent } from '../../types/workflow';
import { IExtraField } from '../../types/template';
import { IHighlightsItem } from '../../types/highlights';
import { isArrayWithItems } from '../../utils/helpers';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../KickoffOutputs';
import { UserData } from '../UserData';
import { getUserFullName } from '../../utils/users';
import { getSnoozedUntilDate } from '../../utils/dateTime';

import { Ellipsis } from './Ellipsis';
import { TruncatedContent } from './utils/TruncatedContent';

import styles from './FeedItem.css';

interface IFeedItemHeaderProps extends IHighlightsItem {}

export function FeedItemHeader({
  attachments,
  text,
  type,
  workflow: { kickoff },
  task,
  delay,
  userId,
}: IFeedItemHeaderProps) {
  const { messages, formatMessage } = useIntl();
  const commentTextRef = useRef<HTMLSpanElement>(null);

  const [isTextExpanded, setIsTextExpanded] = useState(false);
  const [isCommentExpandable, setIsCommentExpandable] = useState(true);

  useEffect(() => {
    const commentTextHeigh = commentTextRef.current?.offsetHeight || 0;

    setIsCommentExpandable(commentTextHeigh > MAX_TRUNCATED_COMMENT_HEIGHT || hasAttachments);
  }, [commentTextRef.current]);

  const hasAttachments = Boolean(text && attachments && isArrayWithItems(attachments));
  const hasCommentText = Boolean(text);
  const MAX_TRUNCATED_COMMENT_HEIGHT = 20 * 5;

  const renderElipsis = () => {
    return <Ellipsis expand={() => setIsTextExpanded(true)} />;
  };

  const renderOutputsContents = () => {
    if (!task) {
      return null;
    }
    const { output: taskOutput } = task;
    const OUTPUTS_MAP: { [key in EWorkflowLogEvent]?: IExtraField[] } = {
      [EWorkflowLogEvent.WorkflowRun]: kickoff?.output,
      [EWorkflowLogEvent.WorkflowComplete]: taskOutput,
      [EWorkflowLogEvent.TaskComplete]: taskOutput,
      [EWorkflowLogEvent.WorkflowsReturned]: taskOutput,
      [EWorkflowLogEvent.TaskRevert]: taskOutput,
    };

    const outputs = OUTPUTS_MAP[type];

    if (!outputs || !isArrayWithItems(outputs)) {
      return null;
    }

    const filteredOutputs = outputs.filter(
      (output) =>
        output.value || output.attachments?.length || output?.selections?.some((selection) => selection.isSelected),
    );

    return (
      <>
        <KickoffOutputs
          outputs={filteredOutputs}
          viewMode={EKickoffOutputsViewModes.Short}
          isTruncated={!isTextExpanded}
        />
        {filteredOutputs.length > 1 && !isTextExpanded && renderElipsis()}
      </>
    );
  };

  const renderAttachments = () => {
    if (!text || !hasAttachments) {
      return null;
    }

    return (
      <>
        <Attachments attachments={attachments} isTruncated={!isTextExpanded} />
        {attachments.length > 1 && renderElipsis()}
      </>
    );
  };

  const renderCommentContent = (params: { isTruncated: boolean }) => {
    if (!text) {
      return null;
    }

    const { isTruncated } = params;

    return (
      <>
        {hasCommentText && (
          <div className={styles['header__comment']}>
            <span className={styles['comment__title']}>{messages['general.comment']}</span>
            <span
              className={classnames(styles['comment__text'], isTextExpanded && styles['comment__text_expanded'])}
              ref={commentTextRef}
            >
              <TruncatedContent isTruncated={isTruncated} maxHeight={MAX_TRUNCATED_COMMENT_HEIGHT}>
                <RichText text={text} />
              </TruncatedContent>
            </span>
          </div>
        )}
        {hasAttachments && !isTruncated && <Attachments attachments={attachments} />}
        {isTruncated && renderElipsis()}
      </>
    );
  };

  const renderTaskCommentContent = () => {
    if (!text) {
      return null;
    }

    const hasOnlyAttachments = hasAttachments && !text;

    if (hasOnlyAttachments) {
      return renderAttachments();
    }

    const shoudShowTruncatedContent = !isTextExpanded && isCommentExpandable;

    return renderCommentContent({ isTruncated: shoudShowTruncatedContent });
  };

  const renderAddedPerformer = () => {
    if (!userId) {
      return null;
    }

    return (
      <div className={styles['changed-performer']}>
        {formatMessage({ id: 'task.log-added-performer' })}
        <UserData userId={userId}>
          {(user) => {
            if (!user) {
              return null;
            }

            return <span className={styles['username']}>{getUserFullName(user, { withAtSign: true })}</span>;
          }}
        </UserData>
      </div>
    );
  };

  const renderRemovedPerformer = () => {
    if (!userId) {
      return null;
    }

    return (
      <div className={styles['changed-performer']}>
        {formatMessage({ id: 'task.log-removed-performer' })}
        <UserData userId={userId}>
          {(user) => {
            if (!user) {
              return null;
            }

            return <span className={styles['username']}>{getUserFullName(user, { withAtSign: true })}</span>;
          }}
        </UserData>
      </div>
    );
  };

  const EVENT_CONTENT_MAP: { [key in EWorkflowLogEvent]?: JSX.Element | null } = {
    [EWorkflowLogEvent.TaskComplete]: renderOutputsContents(),
    [EWorkflowLogEvent.TaskComment]: renderTaskCommentContent(),
    [EWorkflowLogEvent.WorkflowRun]: renderOutputsContents(),
    [EWorkflowLogEvent.WorkflowFinished]: renderTaskCommentContent(),
    [EWorkflowLogEvent.WorkflowComplete]: renderOutputsContents(),
    [EWorkflowLogEvent.WorkflowsReturned]: renderOutputsContents(),
    [EWorkflowLogEvent.TaskRevert]: renderOutputsContents(),
    [EWorkflowLogEvent.AddedPerformer]: renderAddedPerformer(),
    [EWorkflowLogEvent.RemovedPerformer]: renderRemovedPerformer(),
    [EWorkflowLogEvent.WorkflowSnoozedManually]: (
      <>{formatMessage({ id: 'workflows.event-snoozed-until' }, { date: getSnoozedUntilDate(delay || null) })}</>
    ),
    [EWorkflowLogEvent.WorkflowResumed]: <>{formatMessage({ id: 'workflows.event-resumed' })}</>,
  };

  const FeedItemHeaderComponent = EVENT_CONTENT_MAP[type] ?? null;

  return FeedItemHeaderComponent;
}

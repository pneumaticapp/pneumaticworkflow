import React, { useEffect, useRef, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EWorkflowLogEvent } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { Attachments } from '../Attachments';
import { RichText } from '../RichText';

import { Ellipsis } from './Ellipsis';
import { IFeedItemCommentProps } from './types';
import { TruncatedContent } from './utils/TruncatedContent';

import styles from './FeedItem.css';

const MAX_TRUNCATED_COMMENT_HEIGHT = 20 * 5;

export function FeedItemComment({
  attachments,
  isTextExpanded,
  onExpand,
  task,
  text,
  type,
}: IFeedItemCommentProps) {
  const { formatMessage, messages } = useIntl();
  const commentTextRef = useRef<HTMLSpanElement>(null);
  const [isCommentExpandable, setIsCommentExpandable] = useState(true);
  const hasAttachments = Boolean(text && attachments && isArrayWithItems(attachments));

  useEffect(() => {
    const commentTextHeight = commentTextRef.current?.offsetHeight || 0;

    setIsCommentExpandable(commentTextHeight > MAX_TRUNCATED_COMMENT_HEIGHT || hasAttachments);
  }, [attachments, hasAttachments, text]);

  if (!text) {
    return null;
  }

  const isTruncated = !isTextExpanded && isCommentExpandable;

  return (
    <>
      <div className={styles['header__comment']}>
        <span className={styles['comment__title']}>
          {type === EWorkflowLogEvent.TaskRevert
            ? formatMessage({ id: 'task.log-returned' }, { taskName: task?.name })
            : messages['general.comment']}
        </span>
        <span
          className={classnames(styles['comment__text'], isTextExpanded && styles['comment__text_expanded'])}
          ref={commentTextRef}
        >
          <TruncatedContent isTruncated={isTruncated} maxHeight={MAX_TRUNCATED_COMMENT_HEIGHT}>
            <RichText text={text} />
          </TruncatedContent>
        </span>
      </div>
      {hasAttachments && !isTruncated && <Attachments attachments={attachments} />}
      {isTruncated && <Ellipsis expand={onExpand} />}
    </>
  );
}

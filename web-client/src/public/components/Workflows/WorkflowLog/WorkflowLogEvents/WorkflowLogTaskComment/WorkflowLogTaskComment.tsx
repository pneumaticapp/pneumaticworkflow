/* eslint-disable jsx-a11y/control-has-associated-label */
import React, { useEffect, useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { InView } from 'react-intersection-observer';
import data from '@emoji-mart/data';
import Picker from '@emoji-mart/react';

import { useClickOutside } from '../../../../../hooks/useClickOutside';
import { IDeleteComment } from '../../../../../api/workflows/deleteComment';
import { Avatar } from '../../../../UI/Avatar';
import { EWorkflowStatus, IWorkflowLogItem } from '../../../../../types/workflow';
import { getUserFullName } from '../../../../../utils/users';
import { RichText } from '../../../../RichText';
import { Attachments } from '../../../../Attachments';
import { UserData } from '../../../../UserData';
import {
  AddEmojiIcon,
  CommentDeleteIcon,
  CommentInfoIcon,
  CommentWatchedIcon,
  CommenеEditCancelIcon,
  CommenеEditDoneIcon,
} from '../../../../icons';
import { RichEditorContainer } from '../../../../RichEditor';
import { IAccount, TUserListItem } from '../../../../../types/user';
import { useStatePromise } from '../../../../../hooks/useStatePromise';
import { TUploadedFile } from '../../../../../utils/uploadFiles';
import { IEditComment } from '../../../../../api/workflows/editComment';
import { IWatchedComment } from '../../../../../api/workflows/watchedComment';
import { Tooltip } from '../../../../UI';
import { ICreateReaction } from '../../../../../api/workflows/createReactionComment';
import { IDeleteReaction } from '../../../../../api/workflows/deleteReactionComment';

import styles from './WorkflowLogTaskComment.css';
import { DateFormat } from '../../../../UI/DateFormat';

export function WorkflowLogTaskComment({
  id,
  workflowStatus,
  currentUserId,
  status,
  text,
  watched,
  reactions,
  userId,
  created,
  attachments,
  isOnlyAttachmentsShown = false,
  workflowModal,
  editComment,
  deleteComment,
  watchedComment,
  createReactionComment,
  deleteReactionComment,
}: TWorkflowLogTaskCommentProps) {
  const { formatMessage } = useIntl();

  const clickRef = useRef<HTMLButtonElement>(null);
  const [isShowTooltipEmoji, setIsShowTooltipEmoji] = useState(false);
  const [isShowEmoji, setIsShowEmoji] = useState(false);
  const [isWatched, setIsWatched] = useState(false);
  const [isDelete, setIsDelete] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [commentText, setCommentText] = useStatePromise('');
  const [filesToUpload, setFilesToUpload] = useStatePromise<TUploadedFile[]>([]);

  useClickOutside(clickRef, () => {
    setIsShowTooltipEmoji(false);
  });

  useEffect(() => {
    setTimeout(() => {
      if (!isShowTooltipEmoji) {
        setIsShowEmoji(false);
      }

      setIsShowEmoji(true);
    }, 500);
  }, [isShowTooltipEmoji]);

  const handleReactionComment = (value: string) => {
    if (workflowStatus === EWorkflowStatus.Finished) return;

    if (value in reactions && reactions[value].indexOf(currentUserId as Pick<IAccount, 'id'>) !== -1) {
      deleteReactionComment({ id, value });
    } else {
      createReactionComment({ id, value });
    }

    setIsShowTooltipEmoji(false);
  };

  const handleWatchedComment = (inView: boolean) => {
    if (
      !isWatched &&
      inView &&
      currentUserId !== userId &&
      status !== ECommentStatus.Deleted &&
      workflowStatus !== EWorkflowStatus.Finished
    ) {
      watchedComment({ id });
      setIsWatched(true);
    }
  };

  const handleEditComment = () => {
    setIsEdit(false);

    if (commentText && commentText !== text) {
      editComment({ id, text: commentText, attachments: filesToUpload });
    }

    setFilesToUpload([]);
    setCommentText('');
  };

  const handleDeleteComment = () => {
    deleteComment({ id });
    setIsDelete(false);
  };

  const renderDeleteButton = () => {
    return (
      <div>
        {isDelete ? (
          <div className={styles['comment__delete-sure']}>
            <p>
              {formatMessage({ id: 'workflows.comment-delete-sure' })}&nbsp;{' '}
              <button type="button" onClick={() => setIsDelete(false)}>
                {formatMessage({ id: 'workflows.comment-delete-no' })}
              </button>
              &nbsp;/&nbsp;
              <button type="button" onClick={handleDeleteComment}>
                {formatMessage({ id: 'workflows.comment-delete-yes' })}
              </button>
            </p>
          </div>
        ) : (
          <button
            type="button"
            aria-label={formatMessage({ id: 'workflows.comment-delete' })}
            className={styles['comment__delete']}
            onClick={() => setIsDelete(true)}
          >
            {formatMessage({ id: 'workflows.comment-delete' })}
          </button>
        )}
      </div>
    );
  };

  const renderActions = () => {
    if (currentUserId !== userId || workflowStatus === EWorkflowStatus.Finished) return null;

    return (
      <div className={styles['comment__actions']}>
        {renderDeleteButton()}
        {!isDelete && (
          <button
            type="button"
            aria-label={formatMessage({ id: 'workflows.comment-edit' })}
            className={styles['comment__edit']}
            onClick={() => setIsEdit(true)}
          >
            {formatMessage({ id: 'workflows.comment-edit' })}
          </button>
        )}
      </div>
    );
  };

  const renderHeader = (type: string, user: TUserListItem) => {
    if (isEdit) return null;

    const typeMap: { [ECommentStatus: string]: React.ReactNode } = {
      [ECommentStatus.Created]: (
        <header className={styles['comment__info']}>
          <h3 className={styles['comment__user']}>{getUserFullName(user)}</h3>
          <div className={styles['comment__icon']}>
            <CommentInfoIcon />
          </div>
          <time dateTime={created} className={styles['comment__date']}>
            <DateFormat date={created} />
          </time>
          {renderActions()}
        </header>
      ),
      [ECommentStatus.Updated]: (
        <header className={styles['comment__info']}>
          <h3 className={styles['comment__user']}>{getUserFullName(user)}</h3>
          <div className={styles['comment__icon']}>
            <CommentInfoIcon />
          </div>
          <time dateTime={created} className={styles['comment__date']}>
            <DateFormat date={created} /> ({formatMessage({ id: 'workflows.comment-edited' })})
          </time>
          {renderActions()}
        </header>
      ),
      [ECommentStatus.Deleted]: (
        <header className={styles['comment__info']}>
          <h3 className={styles['comment__user']}>{getUserFullName(user)}</h3>
          <div className={classnames(styles['comment__icon'], styles['is-delete'])}>
            <CommentDeleteIcon />
          </div>
          <time dateTime={created} className={styles['comment__date']}>
            <DateFormat date={created} />
          </time>
        </header>
      ),
    };

    return typeMap[type];
  };

  const commentField = () => {
    return (
      <>
        {!isOnlyAttachmentsShown &&
          (!isEdit ? (
            <div className={styles['comment__content']}>
              <RichText text={text} />
            </div>
          ) : (
            <RichEditorContainer
              defaultValue={text || ''}
              handleChange={setCommentText}
              cancelIcon={<CommenеEditCancelIcon />}
              submitIcon={<CommenеEditDoneIcon />}
              onCancel={() => setIsEdit(false)}
              onSubmit={() => handleEditComment()}
              accountId={userId as number}
            />
          ))}
        <Attachments attachments={attachments} isEdit={false} />
      </>
    );
  };

  const renderComment = (type: string) => {
    const typeMap: { [ECommentStatus: string]: React.ReactNode } = {
      [ECommentStatus.Created]: commentField(),
      [ECommentStatus.Updated]: commentField(),
      [ECommentStatus.Deleted]: (
        <div className={styles['comment__content']}>
          <RichText text={formatMessage({ id: 'workflows.comment-deleted' })} />
        </div>
      ),
    };

    return typeMap[type];
  };

  const renderListUsers = (list: Pick<IAccount, 'id'>[]) => {
    return (
      <ul className={styles['comment__watch-list']}>
        {list.map((userWatch) => {
          return (
            <UserData userId={userWatch as number}>
              {(user) => {
                if (!user) return null;
                const userName = getUserFullName(user);

                return <li>{userName}</li>;
              }}
            </UserData>
          );
        })}
      </ul>
    );
  };

  const renderReaction = () => {
    return Object.entries(reactions).map(([value, users]) => {
      return (
        <Tooltip
          content={renderListUsers(users)}
          containerClassName={classnames(styles['comment__footer-item'], workflowModal && styles['is-modal'])}
        >
          <button type="button" onClick={() => handleReactionComment(value)} className={styles['comment__footer-item']}>
            <div className={styles['comment__footer-item-emoji']}>{value}</div>
            <span>{users.length}</span>
          </button>
        </Tooltip>
      );
    });
  };

  const renderFooter = () => {
    if (status === ECommentStatus.Deleted) return null;

    return (
      <footer className={styles['comment__footer']} ref={clickRef}>
        {watched.length ? (
          <Tooltip
            content={renderListUsers(watched.map((value) => value.userId))}
            containerClassName={classnames(styles['comment__footer-item'], workflowModal && styles['is-modal'])}
          >
            <div>
              <CommentWatchedIcon />
              <span>{watched.length}</span>
            </div>
          </Tooltip>
        ) : (
          <div className={classnames(styles['comment__footer-item'], workflowModal && styles['is-modal'])}>
            <CommentWatchedIcon />
            <span>{watched.length}</span>
          </div>
        )}

        {renderReaction()}

        {workflowStatus !== EWorkflowStatus.Finished ? (
          <Tooltip
            visible={isShowTooltipEmoji}
            size="auto"
            containerClassName={classnames(styles['comment__footer-item'], styles['is-add-emoji'])}
            content={
              isShowEmoji && (
                <Picker
                  data={data}
                  theme="dark"
                  searchPosition="none"
                  previewPosition="none"
                  onEmojiSelect={({ native }: { native: string }) => handleReactionComment(native)}
                />
              )
            }
          >
            <button type="button" onClick={() => setIsShowTooltipEmoji(!isShowTooltipEmoji)}>
              <AddEmojiIcon />
            </button>
          </Tooltip>
        ) : null}
      </footer>
    );
  };

  return (
    <UserData userId={userId}>
      {(user) => {
        if (!user) {
          return null;
        }

        return (
          <InView as="article" className={styles['comment']} onChange={(inView) => handleWatchedComment(inView)}>
            <div className={styles['comment__avatar']}>
              <Avatar user={user} size="lg" sizeMobile="sm" />
            </div>
            <div className={styles['comment__body']}>
              {renderHeader(status, user)}
              {renderComment(status)}
              {renderFooter()}
            </div>
          </InView>
        );
      }}
    </UserData>
  );
}

export enum ECommentStatus {
  Created = 'created',
  Deleted = 'deleted',
  Updated = 'updated',
}

export type TWorkflowLogTaskCommentProps = Pick<
  IWorkflowLogItem,
  'id' | 'text' | 'userId' | 'status' | 'created' | 'attachments' | 'watched' | 'reactions'
> & {
  currentUserId: number;
  workflowModal: boolean;
  workflowStatus: EWorkflowStatus;
  isOnlyAttachmentsShown?: boolean;
  editComment(payload: IEditComment): void;
  deleteComment(payload: IDeleteComment): void;
  watchedComment(payload: IWatchedComment): void;
  createReactionComment(payload: ICreateReaction): void;
  deleteReactionComment(payload: IDeleteReaction): void;
};

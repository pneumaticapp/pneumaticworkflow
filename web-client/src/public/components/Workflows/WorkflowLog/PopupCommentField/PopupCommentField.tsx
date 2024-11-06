import * as React from 'react';
import { useIntl } from 'react-intl';

import { RichEditorContainer } from '../../../RichEditor';
import { Avatar } from '../../../UI/Avatar';
import { IAuthUser } from '../../../../types/redux';
import { TUploadedFile } from '../../../../utils/uploadFiles';
import { ISendWorkflowLogComment } from '../../../../redux/actions';
import { useStatePromise } from '../../../../hooks/useStatePromise';
import { isArrayWithItems } from '../../../../utils/helpers';

import styles from './PopupCommentField.css';

export interface IPopupCommentFieldProps {
  user: IAuthUser;
  sendComment({ text, attachments }: ISendWorkflowLogComment): void;
}

export type TPopupCommentFieldProps = IPopupCommentFieldProps;

export function PopupCommentField({ user, sendComment }: TPopupCommentFieldProps) {
  const { formatMessage } = useIntl();

  const [commentText, setCommentText] = useStatePromise('');
  const [filesToUpload, setFilesToUpload] = useStatePromise<TUploadedFile[]>([]);

  const hasText = Boolean(commentText && commentText.trim());

  const handleSendComment = () => {
    if (!hasText && !isArrayWithItems(filesToUpload)) {
      return;
    }

    sendComment({ text: commentText, attachments: filesToUpload });
    setFilesToUpload([]);
    setCommentText('');
  };

  const placeholder = formatMessage({ id: 'workflows.log-comment-field-placeholder' });

  return (
    <div className={styles['comment-field']}>
      <Avatar
        user={user}
        className={styles['comment-field__avatar']}
        containerClassName={styles['comment-field__avatar-container']}
      />
      <div className={styles['comment-field__workarea']}>
        <RichEditorContainer
          placeholder={placeholder}
          handleChange={setCommentText}
          onSubmit={handleSendComment}
          className={styles['editor']}
          accountId={user.id}
        />
      </div>
    </div>
  );
}

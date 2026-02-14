import * as React from 'react';
import { useIntl } from 'react-intl';

import { RichEditor, type IRichEditorHandle } from '../../../RichEditor/lexical';
import { Avatar } from '../../../UI/Avatar';
import { IAuthUser } from '../../../../types/redux';
import { TUploadedFile } from '../../../../utils/uploadFiles';
import { ISendWorkflowLogComment } from '../../../../redux/actions';
import { useStatePromise } from '../../../../hooks/useStatePromise';
import { isArrayWithItems } from '../../../../utils/helpers';

import styles from './PopupCommentField.css';

export interface IPopupCommentFieldProps {
  user: IAuthUser;
  sendComment({ text, attachments, taskId }: ISendWorkflowLogComment): void;
  taskId?: number;
}

export type TPopupCommentFieldProps = IPopupCommentFieldProps;

export function PopupCommentField({ user, sendComment, taskId }: TPopupCommentFieldProps) {
  const { formatMessage } = useIntl();
  const editorRef = React.useRef<IRichEditorHandle>(null);

  const [commentText, setCommentText] = useStatePromise('');
  const [filesToUpload, setFilesToUpload] = useStatePromise<TUploadedFile[]>([]);

  const hasText = Boolean(commentText && commentText.trim());

  const handleSendComment = () => {
    if (!hasText && !isArrayWithItems(filesToUpload)) {
      return;
    }

    sendComment({ text: commentText, attachments: filesToUpload, taskId });
    setFilesToUpload([]);
    setCommentText('');
    editorRef.current?.clearContent?.();
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
        <RichEditor
          ref={editorRef}
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

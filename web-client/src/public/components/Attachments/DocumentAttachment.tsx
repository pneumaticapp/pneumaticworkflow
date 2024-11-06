/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { DeleteBoldIcon, DocumentInfoIcon, VideoInfoIcon } from '../icons';
import { TUploadedFile } from '../../utils/uploadFiles';
import { getAttachmentTypeByFilename } from './utils/getAttachmentType';

import styles from './Attachments.css';

export interface IDocumentAttachment extends Pick<TUploadedFile, 'name' | 'url'> {
  isDeleting?: boolean;
  isEdit: boolean;
  className?: string;
  isClickable?: boolean;
  deleteFile?(): void;
}

export function DocumentAttachment({
  deleteFile,
  isDeleting,
  isEdit,
  name,
  url,
  className,
  isClickable = true,
}: IDocumentAttachment) {
  const onDeleteIconClick: React.MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    event.preventDefault();

    if (deleteFile) {
      deleteFile();
    }
  };

  const Icon = getAttachmentTypeByFilename(name) === 'video'
    ? VideoInfoIcon
    : DocumentInfoIcon;

  return (
    <span
      className={classnames(
        className,
        styles['documents-list__document-container'],
        isDeleting && styles['documents-list__document-container_loading'],
      )}
    >
      <a
        href={url}
        target="_blank"
        className={classnames(styles['document'], !isClickable && styles['document_not-clickable'])}
        onClick={event => !isClickable && event.preventDefault()}
      >
        <Icon className={styles['document__icon']} />
        <span className={styles['document__filename']}>{name}</span>
      </a>
      {isEdit &&
        <button
          className={styles['document__delete-button']}
          onClick={onDeleteIconClick}
        >
          <DeleteBoldIcon />
        </button>
      }
    </span>
  );
}

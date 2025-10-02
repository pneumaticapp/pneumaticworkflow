/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { isArrayWithItems } from '../../utils/helpers';
import { TUploadedFile } from '../../utils/uploadFiles';

import { DocumentAttachment } from './DocumentAttachment';
import { ImageAttachment } from './ImageAttachment';
import styles from './Attachments.css';

export interface ICommentAttachments {
  attachments: TUploadedFile[];
  isEdit?: boolean;
  isUploading?: boolean;
  deletingFilesIds?: number[];
  isTruncated?: boolean;
  deleteFile?(id: number): () => void;
}

export function Attachments({
  attachments,
  isEdit = false,
  isUploading,
  deletingFilesIds = [],
  deleteFile,
  isTruncated,
}: ICommentAttachments) {
  const hasFiles = isArrayWithItems(attachments);

  if (!hasFiles) {
    return null;
  }

  const images = attachments.filter(file => file.thumbnailUrl);
  const hasImages = Boolean(images.length);
  const documents = attachments.filter(file => !file.thumbnailUrl);
  const hasDocuments = Boolean(documents.length);
  const onlyOneDocumentAndImage = images.length === 1 && documents.length === 1;

  if (isTruncated) {
    const firstAttachment = attachments[0];
    const isImage = Boolean(firstAttachment.thumbnailUrl);

    return isImage
      ? <ImageAttachment
        url={firstAttachment.url}
        thumbnailUrl={firstAttachment.thumbnailUrl!}
        deleteFile={deleteFile && deleteFile(firstAttachment.id)}
        isEdit={isEdit}
        key={firstAttachment.id}
        isDeleting={deletingFilesIds.some(id => id === firstAttachment.id)}
      />
      : <DocumentAttachment
        {...firstAttachment}
        deleteFile={deleteFile && deleteFile(firstAttachment.id)}
        isEdit={isEdit}
        key={firstAttachment.id}
        isDeleting={deletingFilesIds.some(id => id === firstAttachment.id)}
      />;
  }

  return (
    <div className={classnames(
      styles['comment-attachments'],
      isUploading && styles['comment-attachments_loading'],
    )}>
      {hasImages &&
        <div className={classnames(
          styles['comment-attachments__images-list'],
          onlyOneDocumentAndImage && styles['comment-attachments__images-list_padded'],
        )}>
          {images.map(image => (
            <ImageAttachment
              url={image.url}
              thumbnailUrl={image.thumbnailUrl!}
              deleteFile={deleteFile && deleteFile(image.id)}
              isEdit={isEdit}
              key={image.id}
              isDeleting={deletingFilesIds.some(id => id === image.id)}
            />
          ))}
        </div>
      }
      {hasDocuments &&
        <div className={styles['comment-attachments__documents-list']}>
          {documents.map(document => (
            <DocumentAttachment
              {...document}
              deleteFile={deleteFile && deleteFile(document.id)}
              isEdit={isEdit}
              key={document.id}
              isDeleting={deletingFilesIds.some(id => id === document.id)}
            />
          ))}
        </div>
      }
    </div>
  );
}

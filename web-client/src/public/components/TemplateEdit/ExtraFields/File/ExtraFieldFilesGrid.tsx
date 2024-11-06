/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { isArrayWithItems } from '../../../../utils/helpers';
import { TUploadedFile } from '../../../../utils/uploadFiles';
import { Loader } from '../../../UI/Loader';

import { ExtraFieldFileDocument } from './ExtraFieldFileDocument';
import { ExtraFieldFileImage } from './ExtraFieldFileImage';

import styles from './ExtraFieldFile.css';

export interface IExtraFieldFilesGrid {
  attachments: TUploadedFile[];
  isEdit?: boolean;
  isUploading?: boolean;
  deleteFile?(id: number): () => void;
}

export function ExtraFieldFilesGrid({
  attachments,
  isEdit = false,
  isUploading,
  deleteFile,
}: IExtraFieldFilesGrid) {
  const hasFiles = isArrayWithItems(attachments);

  if (!hasFiles && !isUploading) {
    return null;
  }

  const images = attachments.filter(file => file.thumbnailUrl);
  const hasImages = Boolean(images.filter(({ isRemoved }) => !isRemoved).length);
  const documents = attachments.filter(file => !file.thumbnailUrl);
  const hasDocuments = Boolean(documents.filter(({ isRemoved }) => !isRemoved).length);

  return (
    <div className={classnames(
      (hasDocuments || hasImages || isUploading) && styles['extra-field-files-grid'],
      isUploading && styles['extra-field-files-grid_loading'],
    )}>
      {Boolean(isUploading) &&
        <Loader isLoading={Boolean(isUploading)} />
      }
      {hasImages &&
        <div className={styles['extra-field-files-grid__images-grid']}>
          {images.map(image => (
            <ExtraFieldFileImage
              {...image}
              deleteFile={deleteFile && deleteFile(image.id)}
              isEdit={isEdit}
              key={image.id}
            />
          ))}
        </div>
      }
      {hasDocuments &&
        <div className={styles['extra-field-files-grid__documents-grid']}>
          {documents.map(document => (
            <ExtraFieldFileDocument
              {...document}
              deleteFile={deleteFile && deleteFile(document.id)}
              isEdit={isEdit}
              key={document.id}
            />
          ))}
        </div>
      }
    </div>
  );
}

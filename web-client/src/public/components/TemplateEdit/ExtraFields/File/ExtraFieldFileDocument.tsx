/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { DeleteBoldIcon } from '../../../icons';
import { TUploadedFile } from '../../../../utils/uploadFiles';

import styles from './ExtraFieldFile.css';

export interface IExtraFieldFileDocument extends TUploadedFile {
  isEdit: boolean;
  deleteFile?(): void;
}

export function ExtraFieldFileDocument({ deleteFile, isRemoved, isEdit, name, url }: IExtraFieldFileDocument) {
  if (isRemoved) {
    return null;
  }

  const handleDeleteIconClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.stopPropagation();
    e.preventDefault();

    if (deleteFile) {
      deleteFile();
    }
  };

  return (
    <span
      className={classnames(styles['extra-field-files-document-grid__document-container'])}
    >
      <a
        href={url}
        target="_blank"
        className={classnames(styles['extra-field-document'], isEdit && styles['document_edit'])}
      >
        {name}
      </a>
      {isEdit &&
        <button
          className={styles['extra-field-document__delete-button']}
          onClick={handleDeleteIconClick}
          type="button"
        >
          <DeleteBoldIcon className={styles['delete-button']} />
        </button>
      }
    </span>
  );
}

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { useDispatch } from 'react-redux';

import { DeleteBoldIcon } from '../../../icons';
import { TUploadedFile } from '../../../../utils/uploadFiles';
import { openFullscreenImage } from '../../../../redux/actions';

import styles from './ExtraFieldFile.css';

export interface IExtraFieldFileImage extends TUploadedFile {
  isEdit: boolean;
  deleteFile?(): void;
}

export function ExtraFieldFileImage({ deleteFile, isRemoved, isEdit, thumbnailUrl, url }: IExtraFieldFileImage) {
  if (isRemoved) {
    return null;
  }

  const dispatch = useDispatch();

  const handleDeleteIconClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.preventDefault();
    e.stopPropagation();

    if (deleteFile) {
      deleteFile();
    }
  };

  return (
    <div className={classnames(styles['images-list__image-container'])}>
      {isEdit &&
        <button
          className={styles['extra-field-image__delete-button']}
          onClick={handleDeleteIconClick}
          type="button"
        >
          <DeleteBoldIcon className={styles['delete-button']} />
        </button>
      }
      <button
        className={styles['extra-field-image__link']}
        onClick={() => dispatch(openFullscreenImage({ url }))}
      >
        <img
          src={thumbnailUrl}
          className={styles['extra-field-image']}
        />
      </button>
    </div>
  );
}

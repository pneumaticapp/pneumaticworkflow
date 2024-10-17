/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { useDispatch } from 'react-redux';

import { DeleteBoldIcon } from '../icons';
import { Loader } from '../UI/Loader';
import { openFullscreenImage } from '../../redux/actions';

import styles from './Attachments.css';

export interface IImageAttachment {
  isDeleting?: boolean;
  isEdit?: boolean;
  thumbnailUrl: string;
  url?: string;
  className?: string;
  deleteFile?(): void;
}

export function ImageAttachment({ deleteFile, isDeleting, isEdit, thumbnailUrl, url, className }: IImageAttachment) {
  const dispatch = useDispatch();

  const onDeleteIconClick: React.MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    event.preventDefault();

    if (deleteFile) {
      deleteFile();
    }
  };

  const renderImage = () => {
    if (!url) {
      return (
        <img
          src={thumbnailUrl}
          className={styles['image']}
        />
      );
    }

    return (
      <button
className={styles['image__link']}
        onClick={() => dispatch(openFullscreenImage({ url }))}
      >
        <img
          src={thumbnailUrl}
          className={styles['image']}
        />
      </button>
    );
  };

  return (
    <div
      className={classnames(
        className,
        styles['images-list__image-container'],
        isDeleting && styles['images-list__image-container_loading'],
      )}
    >
      <Loader isLoading={Boolean(isDeleting)} />
      {isEdit &&
        <button
          aria-label="Delete image"
          className={styles['image__delete-button']}
          onClick={onDeleteIconClick}
        >
          <DeleteBoldIcon />
        </button>
      }
      {renderImage()}
    </div>
  );
}

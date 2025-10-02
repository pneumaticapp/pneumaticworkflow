/* eslint-disable */
/* prettier-ignore */
import React, { ReactElement } from 'react';
import * as classnames from 'classnames';

import { IAttachmentProps } from '..';
import { DeleteBoldIcon } from '../../../../icons';
import { TEditorAttachment } from '../../types';

import styles from './Video.css';

export function Video(props: IAttachmentProps): ReactElement {
  const { block, className, ...otherProps } = props;
  const { contentState, deleteAttachment, ...elementProps } = otherProps;
  const { url } = contentState.getEntity(block.getEntityAt(0)).getData() as TEditorAttachment;

  const handleDelete: React.MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    event.preventDefault();
    deleteAttachment(block);
  };

  return (
    <div {...elementProps} onClick={e => e.stopPropagation()}>
      <div className={styles['container']}>
        <video
          src={url}
          preload="auto"
          className={classnames(styles['video'], className)}
        />
        <button
          aria-label="Delete video"
          className={styles['delete']}
          onClick={handleDelete}
        >
          <DeleteBoldIcon />
        </button>
      </div>
    </div>
  );
}

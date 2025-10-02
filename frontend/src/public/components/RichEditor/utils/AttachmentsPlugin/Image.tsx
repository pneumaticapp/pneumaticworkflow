/* eslint-disable */
/* prettier-ignore */
import React, { ReactElement } from 'react';

import { ImageAttachment } from '../../../Attachments/ImageAttachment';
import { IAttachmentProps } from '.';
import { TEditorAttachment } from '../types';

export function Image(props: IAttachmentProps): ReactElement {
  const { block, className, ...otherProps } = props;
  const { contentState, deleteAttachment, ...elementProps } = otherProps;
  const { url } = contentState.getEntity(block.getEntityAt(0)).getData() as TEditorAttachment;

  return (
    <div {...elementProps} >
      <ImageAttachment
        thumbnailUrl={url}
        className={className}
        isEdit
        deleteFile={() => deleteAttachment(block)}
      />
    </div>
  );
}

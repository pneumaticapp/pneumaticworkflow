/* eslint-disable */
/* prettier-ignore */
import React, { ReactElement } from 'react';

import { IAttachmentProps } from '.';
import { DocumentAttachment } from '../../../Attachments/DocumentAttachment';
import { TEditorAttachment } from '../types';

export function File(props: IAttachmentProps): ReactElement {
  const { block, className, ...otherProps } = props;
  const { contentState, deleteAttachment, ...elementProps } = otherProps;
  const { url, name } = contentState.getEntity(block.getEntityAt(0)).getData() as TEditorAttachment;

  return (
    <div {...elementProps} onClick={e => e.stopPropagation()}>
      <DocumentAttachment
        className={className}
        isEdit
        deleteFile={() => deleteAttachment(block)}
        name={name || url}
        url={url}
        isClickable={false}
      />
    </div>
  );
}

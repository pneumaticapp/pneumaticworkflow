import React, { memo } from 'react';
import classnames from 'classnames';

import { getForegroundClass } from '../../../../UI/Fields/common/utils/getForegroundClass';
import type { IEditorHeaderProps } from './types';

import styles from './EditorHeader.css';



function EditorHeaderComponent({ title, foregroundColor }: IEditorHeaderProps): React.ReactElement | null {
  if (!title) return null;

  return (
    <div className={classnames(styles['title'], getForegroundClass(foregroundColor))}>
      {title}
    </div>
  );
}

export const EditorHeader = memo(EditorHeaderComponent);

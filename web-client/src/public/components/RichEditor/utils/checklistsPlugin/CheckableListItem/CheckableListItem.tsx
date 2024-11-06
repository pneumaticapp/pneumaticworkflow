import React from 'react';
import { EditorBlock, SelectionState, ContentState, ContentBlock } from 'draft-js';
import type { List } from 'immutable';

import { Checkbox } from '../../../../UI';

import styles from './CheckableListItem.css';

type TCheckableListItemProps = {
  contentState: ContentState;
  block: ContentBlock;
  customStyleMap: Object;
  customStyleFn: Function;
  tree: List<any>;
  selection: SelectionState;
  forceSelection: boolean;
  blockStyleFn: Function;
  offsetKey: string;
};

export const CheckableListItem: React.FunctionComponent<TCheckableListItemProps> = (props: TCheckableListItemProps) => {
  const { offsetKey } = props;

  return (
    <div className={styles['checkable-list-item-block']} data-offset-key={offsetKey}>
      <div
        className={styles['checkable-list-item-block__checkbox']}
        contentEditable={false}
        suppressContentEditableWarning
      >
        <Checkbox
          containerClassName={styles['checkable-list-item-block__checkbox-inner']}
          checked={false}
        />
      </div>
      <div className={styles['checkable-list-item-block__text']}>
        <EditorBlock {...props} />
      </div>
    </div>
  );
};

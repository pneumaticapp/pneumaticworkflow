/* eslint-disable */
/* prettier-ignore */
import { EditorState } from 'draft-js';
import { filterEditorState } from 'draftjs-filters';
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';

import { CUSTOM_EDITOR_ENTITES, EEditorBlock, EEditorStyle } from './types';

export const stripUnsupportedStyles = (nextState: EditorState, currentState: EditorState) => {
  const shouldFilterPaste =
      nextState.getCurrentContent() !== currentState.getCurrentContent() &&
      nextState.getLastChangeType() === 'insert-fragment';

  if (!shouldFilterPaste) {
    return nextState;
  }

  const normalizedState = filterEditorState(
    {
      blocks: [EEditorBlock.OrderedListItem, EEditorBlock.UnorderedListItem, CHECKABLE_LIST_ITEM],
      styles: [EEditorStyle.Bold, EEditorStyle.Italic],
      entities: CUSTOM_EDITOR_ENTITES.map(type => ({ type })),
      maxNesting: 1,
      whitespacedCharacters: [],
    },
    nextState,
  );

  return normalizedState;
};

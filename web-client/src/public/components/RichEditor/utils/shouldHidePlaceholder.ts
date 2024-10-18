import { EditorState } from 'draft-js';

import { EEditorBlock } from './types';

export const shouldHidePlaceholder = (editorState: EditorState) => {
  const contentState = editorState.getCurrentContent();

  return contentState.hasText() || contentState.getBlockMap().first().getType() !== EEditorBlock.Unstyled;
};

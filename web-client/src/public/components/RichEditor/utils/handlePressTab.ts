/* eslint-disable */
/* prettier-ignore */
import { EditorState, RichUtils } from 'draft-js';
import * as React from 'react';

const MAX_LIST_DEPTH = 2;

export const handlePressTab = (
  e: React.KeyboardEvent<{}>,
  editorState: EditorState,
  handleChange: (editorState: EditorState) => void,
) => {
  const newEditorState = RichUtils.onTab(e, editorState, MAX_LIST_DEPTH);
  if (newEditorState !== editorState) {
    handleChange(newEditorState);
  }
};

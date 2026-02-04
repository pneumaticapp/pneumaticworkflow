import { EditorState, Modifier } from 'draft-js';

import { EEditorBlock } from './types';

const UNORDERED_PREFIX = '- ';
const ORDERED_PREFIX_MATCH = /^(\d+\.\s)/;

export function applyListShortcut(editorState: EditorState): EditorState {
  if (editorState.getLastChangeType() !== 'insert-characters') {
    return editorState;
  }

  const selection = editorState.getSelection();
  const content = editorState.getCurrentContent();
  const blockKey = selection.getStartKey();
  const block = content.getBlockForKey(blockKey);

  if (block.getType() !== EEditorBlock.Unstyled) {
    return editorState;
  }

  const text = block.getText();
  let prefixLength: number;
  let listType: string;

  if (text.startsWith(UNORDERED_PREFIX)) {
    prefixLength = UNORDERED_PREFIX.length;
    listType = EEditorBlock.UnorderedListItem;
  } else {
    const match = text.match(ORDERED_PREFIX_MATCH);
    if (!match) return editorState;
    prefixLength = match[1].length;
    listType = EEditorBlock.OrderedListItem;
  }

  const replaceRange = selection.merge({
    anchorOffset: 0,
    focusOffset: prefixLength,
  });

  let newContent = Modifier.replaceText(content, replaceRange, '');
  const collapsedAtStart = selection.merge({
    anchorOffset: 0,
    focusOffset: 0,
  });
  newContent = Modifier.setBlockType(newContent, collapsedAtStart, listType);

  const newState = EditorState.push(editorState, newContent, 'change-block-type');
  return EditorState.forceSelection(newState, collapsedAtStart);
}

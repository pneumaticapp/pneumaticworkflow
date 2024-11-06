import { EditorState, SelectionState } from 'draft-js';

export function getSearchText(
  editorState: EditorState,
  selection: SelectionState,
) {
  const anchorKey = selection.getAnchorKey();
  const anchorOffset = selection.getAnchorOffset();
  const currentContent = editorState.getCurrentContent();
  const currentBlock = currentContent.getBlockForKey(anchorKey);
  const blockText = currentBlock.getText();

  const str = blockText.substr(0, anchorOffset);

  return str.length;
}

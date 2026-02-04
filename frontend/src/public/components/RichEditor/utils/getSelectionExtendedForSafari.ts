import { EditorState, SelectionState } from 'draft-js';
import { ECustomEditorEntities } from './types';
import { isSafari } from './isSafari';

/**
 * In Safari, when the selection is collapsed at the end of a block that ends with
 * a variable, the variable is often excluded from the native selection and nothing
 * gets copied. We only extend to the full block in that case (cursor = "copy line").
 * When the user has explicitly selected a range, we do not extend so partial copy works.
 */
export function getSelectionExtendedForSafari(editorState: EditorState): SelectionState {
  const selection = editorState.getSelection();
  if (!isSafari()) {
    return selection;
  }

  // Only extend when selection is collapsed (cursor); never extend a real selection.
  if (!selection.isCollapsed()) {
    return selection;
  }

  const contentState = editorState.getCurrentContent();
  const blockKey = selection.getAnchorKey();
  const block = contentState.getBlockForKey(blockKey);
  const blockLength = block.getLength();

  const offset = selection.getAnchorOffset();
  if (blockLength === 0) return selection;
  if (offset < blockLength - 1) return selection;
  const charAtEnd = block.getCharacterList().get(blockLength - 1);
  const entityKey = charAtEnd.getEntity();
  if (entityKey === null) return selection;
  try {
    const entity = contentState.getEntity(entityKey);
    if (entity.getType() !== ECustomEditorEntities.Variable) return selection;
  } catch {
    return selection;
  }
  return selection.merge({
    anchorKey: blockKey,
    anchorOffset: 0,
    focusKey: blockKey,
    focusOffset: blockLength,
  }) as SelectionState;
}

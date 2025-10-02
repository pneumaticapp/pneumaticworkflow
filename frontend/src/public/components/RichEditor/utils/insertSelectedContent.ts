import { EditorState, Modifier } from "draft-js";

export const insertSelectedContent = (editorState: any, selectedContentState: any) => {
  const contentState = editorState.getCurrentContent();
  const selectionState = editorState.getSelection();

  if (!selectedContentState || !selectedContentState.getBlockMap().size) return editorState;

  const newContentState = Modifier.replaceWithFragment(contentState, selectionState, selectedContentState.getBlockMap());
  let newEditorState = EditorState.push(editorState, newContentState, 'insert-fragment');
  const newSelection = newContentState.getSelectionAfter();
  newEditorState = EditorState.forceSelection(newEditorState, newSelection);

  return newEditorState;
};

/* eslint-disable */
/* prettier-ignore */
import { CharacterMetadata, EditorState, Modifier } from 'draft-js';
import { ECustomEditorEntities } from './types';

export function removeOrphanedEntities(editorState: EditorState) {
  // Need to make sure when an atomic block is deleted that its corresponding entity is, as well
  const atomicTypes: { [key in string]: boolean } = { [ECustomEditorEntities.Image]: true };

  const selectionState = editorState.getSelection();
  const anchorKey = selectionState.getAnchorKey();
  const currentContent = editorState.getCurrentContent();
  const currentContentBlock = currentContent.getBlockForKey(anchorKey);

  const type = currentContentBlock.getType();
  if (type === 'unstyled') {
    let orphan = false;
    currentContentBlock.getCharacterList().forEach((cm: CharacterMetadata) => {
      if (!orphan) {
        const entityKey = cm.getEntity();
        if (entityKey) {
          const entityType = currentContent.getEntity(entityKey).getType();
          if (entityKey && atomicTypes[entityType]) {
            orphan = true;
          }
        }
      }
    });

    if (orphan) {
      // tslint:disable-next-line: no-any
      const newEditorState = editorState as any;
      newEditorState._immutable = newEditorState._immutable.set('allowUndo', false);
      const updatedSelection = selectionState.merge({ anchorOffset: 0 });
      const newContent = Modifier.removeRange(currentContent, updatedSelection, 'forward');

      return EditorState.push(
        newEditorState,
        newContent,
        'remove-range',
      );
    }
  }

  return editorState;
}

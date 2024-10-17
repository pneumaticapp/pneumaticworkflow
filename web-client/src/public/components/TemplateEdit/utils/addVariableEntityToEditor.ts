import { Modifier, EditorState } from 'draft-js';

import { ECustomEditorEntities } from '../../RichEditor/utils/types';
import { getSearchText } from './getSearchText';

export function addVariableEntityToEditor(
  editorState: EditorState,
  variable: {
    title?: string;
    subtitle?: string | React.ReactNode;
    apiName?: string;
  },
) {
  const contentStateWithEntity = editorState
    .getCurrentContent()
    .createEntity(ECustomEditorEntities.Variable, 'IMMUTABLE', variable);
  const entityKey = contentStateWithEntity.getLastCreatedEntityKey();

  const currentSelectionState = editorState.getSelection();
  const index = getSearchText(editorState, currentSelectionState);

  const variableTextSelection = currentSelectionState.merge({
    anchorOffset: index,
    focusOffset: index,
  });

  const variableReplacedContent = Modifier.insertText(
    editorState.getCurrentContent(),
    variableTextSelection,
    `${variable.title}`,
    undefined,
    entityKey,
  );

  const newEditorState = EditorState.push(
    editorState,
    variableReplacedContent,
    'apply-entity',
  );

  return EditorState.forceSelection(
    newEditorState,
    variableReplacedContent.getSelectionAfter(),
  );
}

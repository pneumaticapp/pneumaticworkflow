import { Modifier, EditorState } from 'draft-js';

import { ECustomEditorEntities } from '../../RichEditor/utils/types';
import { getSearchText } from './getSearchText';

const DEFAULT_TITLE = '';

export function addVariableEntityToEditor(
  editorState: EditorState,
  variable: {
    title?: string;
    subtitle?: string | React.ReactNode;
    apiName?: string;
  },
) {
  const safeTitle =
    variable.title != null && String(variable.title).trim() !== ''
      ? String(variable.title)
      : DEFAULT_TITLE;

  const contentStateWithEntity = editorState
    .getCurrentContent()
    .createEntity(ECustomEditorEntities.Variable, 'IMMUTABLE', {
      ...variable,
      title: safeTitle,
    });
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
    safeTitle,
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

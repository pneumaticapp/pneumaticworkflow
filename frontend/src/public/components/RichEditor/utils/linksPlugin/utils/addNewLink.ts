import { Modifier, EditorState } from 'draft-js';
import { ECustomEditorEntities } from '../../types';
import { getSearchText } from '../../../../TemplateEdit/utils/getSearchText';

export function addNewLinkEntity(
  editorState: EditorState,
  linkText: string,
  linkUrl: string,
) {
  const contentStateWithEntity = editorState
    .getCurrentContent()
    .createEntity(ECustomEditorEntities.Link, 'MUTABLE', { url: linkUrl, name: linkText });
  const entityKey = contentStateWithEntity.getLastCreatedEntityKey();

  const currentSelectionState = editorState.getSelection();
  const index = getSearchText(editorState, currentSelectionState);

  const linkTextSelection = currentSelectionState.merge({
    anchorOffset: index,
    focusOffset: index,
  });

  let linkReplacedContent = Modifier.insertText(
    editorState.getCurrentContent(),
    linkTextSelection,
    linkText,
    undefined,
    entityKey,
  );

  const blockKey = linkTextSelection.getAnchorKey();
  const blockSize = editorState
    .getCurrentContent()
    .getBlockForKey(blockKey)
    .getLength();
  if (blockSize === index) {
    linkReplacedContent = Modifier.insertText(
      linkReplacedContent,
      linkReplacedContent.getSelectionAfter(),
      ' ',
    );
  }

  const newEditorState = EditorState.push(
    editorState,
    linkReplacedContent,
    'apply-entity',
  );

  return EditorState.forceSelection(
    newEditorState,
    linkReplacedContent.getSelectionAfter(),
  );
}

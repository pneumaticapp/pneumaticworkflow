/* eslint-disable */
/* prettier-ignore */
import { EditorState, AtomicBlockUtils } from 'draft-js';
import { TAttachmentType } from '../../../../../types/attachments';
import { getAttachmentTypeByUrl } from '../../../../Attachments/utils/getAttachmentType';
import { ECustomEditorEntities, TEditorAttachment } from '../../types';

export const addAttachment = (
  editorState: EditorState,
  file: TEditorAttachment,
): EditorState => {
  const entityType = getAttachmentEntityType(file.url);
  const contentState = editorState.getCurrentContent();
  const contentStateWithEntity = contentState.createEntity(
    entityType,
    'IMMUTABLE',
    {
      id: file.id,
      url: file.url,
      name: file.name,
    } as TEditorAttachment,
  );
  const entityKey = contentStateWithEntity.getLastCreatedEntityKey();
  const newEditorState = AtomicBlockUtils.insertAtomicBlock(
    editorState,
    entityKey,
    ' ',
  );

  return EditorState.forceSelection(
    newEditorState,
    newEditorState.getCurrentContent().getSelectionAfter(),
  );
};

export const getAttachmentEntityType = (fileUrl: string) => {
  const entitiesMap: { [key in TAttachmentType]: ECustomEditorEntities } = {
    file: ECustomEditorEntities.File,
    video: ECustomEditorEntities.Video,
    image: ECustomEditorEntities.Image,
  };

  const attachmentType = getAttachmentTypeByUrl(fileUrl);
  if (!attachmentType) {
    return ECustomEditorEntities.File;
  }

  return entitiesMap[attachmentType];
};

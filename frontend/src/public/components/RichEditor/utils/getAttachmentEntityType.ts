import type { TAttachmentType } from '../../../types/attachments';
import { getAttachmentTypeByUrl } from '../../Attachments/utils/getAttachmentType';
import { ECustomEditorEntities } from './types';

export function getAttachmentEntityType(fileUrl: string): ECustomEditorEntities {
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
}

import type { TAttachmentType } from '../../../types/attachments';
import {
  getAttachmentTypeByFilename,
  getAttachmentTypeByUrl,
} from '../../Attachments/utils/getAttachmentType';
import { ECustomEditorEntities } from './types';

const ATTACHMENT_ENTITIES_MAP: { [key in TAttachmentType]: ECustomEditorEntities } = {
  file: ECustomEditorEntities.File,
  video: ECustomEditorEntities.Video,
  image: ECustomEditorEntities.Image,
};

export function getAttachmentEntityType(fileUrl: string): ECustomEditorEntities {
  const attachmentType = getAttachmentTypeByUrl(fileUrl);
  if (!attachmentType) {
    return ECustomEditorEntities.File;
  }

  return ATTACHMENT_ENTITIES_MAP[attachmentType];
}

/**
 * Determines entity type from a filename (link text).
 * Returns Link when the filename has no recognizable extension,
 * so callers can distinguish "unknown" from "file".
 */
export function getAttachmentEntityTypeByFilename(filename: string): ECustomEditorEntities {
  const attachmentType = getAttachmentTypeByFilename(filename);
  if (!attachmentType) {
    return ECustomEditorEntities.Link;
  }

  return ATTACHMENT_ENTITIES_MAP[attachmentType];
}

/* eslint-disable */
/* prettier-ignore */
import { EditorState } from 'draft-js';
// tslint:disable-next-line: match-default-export-name
import createAttachmentPlugin from './AttachmentsPlugin';

import { uploadFiles } from '../../../utils/uploadFiles';
import { TEditorAttachment } from './types';
import { getAttachmentTypeByUrl } from '../../Attachments/utils/getAttachmentType';

const urlRegex = /((https?|ftp):\/\/)[a-z0-9.-]+\.[a-z]{2,}(\/\S*?(?=\.*(?:\s|,|$)))?/gi;

export const handlePasteAttachments = async (
  e: ClipboardEvent,
  accountId: number,
  editorState: EditorState,
  addAttachment: ReturnType<typeof createAttachmentPlugin>['addAttachment'],
  onStartUpload: () => void,
  onEndUpload: (editorState: EditorState) => void,
) => {
  onStartUpload();
  const text = e.clipboardData?.getData('text/plain') || '';
  const textImageUrls: TEditorAttachment[] = (text
    .match(urlRegex)
    ?.map(url => {
      const fileType = getAttachmentTypeByUrl(url);
      if (!fileType) {
        return null;
      }

      return { url };
    }).filter(Boolean) || []) as TEditorAttachment[];

  const pastedImages = Array.from(e.clipboardData?.items || []).filter(i => {
    const fileTypesRegExps = [/image/, /video/, /text/];

    return fileTypesRegExps.some(regEx => regEx.test(i.type));
  });
  const uploadedImages: TEditorAttachment[] = await uploadFiles(
    pastedImages.map(image => image.getAsFile()).filter(Boolean) as File[],
    accountId,
  );

  const editorStateWithImages = [
    ...uploadedImages,
    ...textImageUrls,
  ].reduce((stateWithImages, uploadedImage) => {
    if (!uploadedImage?.url) {
      return stateWithImages;
    }

    return addAttachment(stateWithImages, uploadedImage);
  }, editorState) as EditorState;

  onEndUpload(editorStateWithImages);

  return true;
};

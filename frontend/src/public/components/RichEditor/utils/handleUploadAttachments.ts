/* eslint-disable */
/* prettier-ignore */
import { logger } from '../../../utils/logger';
import { NotificationManager } from '../../UI/Notifications';
// tslint:disable-next-line: match-default-export-name
import createAttachmentPlugin from './AttachmentsPlugin';
import { uploadFiles } from '../../../utils/uploadFiles';

export async function handleUploadAttachments(
  e: React.ChangeEvent<HTMLInputElement>,
  accountId: number,
  editorState: EditorState,
  addAttachment: ReturnType<typeof createAttachmentPlugin>['addAttachment'],
  onStartUpload: () => void,
  onEndUpload: (editorState: EditorState) => void,
  onError: () => void,
) {
  const { files } = e.target;

  if (!files) {
    return;
  }

  onStartUpload();

  try {
    const uploadedFiles = await uploadFiles(files, accountId);

    const editorStateWithAttachments = uploadedFiles.reduce((stateWithAttachments, uploadedAttachment) => {
      if (!uploadedAttachment?.url) {
        return stateWithAttachments;
      }

      return addAttachment(stateWithAttachments, uploadedAttachment);
    }, editorState) as EditorState;

    onEndUpload(editorStateWithAttachments);
  } catch (error) {
    NotificationManager.warning({ message: 'workflows.tasks-failed-to-upload-files' });
    logger.error(error);
    onError();
  }
}

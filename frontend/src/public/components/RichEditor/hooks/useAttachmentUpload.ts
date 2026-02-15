import { useCallback } from 'react';
import type { MutableRefObject } from 'react';
import type { LexicalEditor } from 'lexical';
import { uploadFiles } from '../../../utils/uploadFiles';
import { getAttachmentTypeByUrl } from '../../Attachments/utils/getAttachmentType';
import { NotificationManager } from '../../UI/Notifications';
import { INSERT_ATTACHMENT_COMMAND } from '../plugins';

const UPLOAD_ERROR_MESSAGE_KEY = 'workflows.tasks-failed-to-upload-files';

function hasUrl(
  att: { url?: string } | undefined,
): att is NonNullable<typeof att> & { url: string } {
  return Boolean(att?.url);
}

export function useAttachmentUpload(
  editorRef: MutableRefObject<LexicalEditor | null>,
  accountId: number | undefined,
): (e: React.ChangeEvent<HTMLInputElement>) => Promise<void> {
  return useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const { files } = e.target;
      if (!files?.length) return;

      const editor = editorRef.current;
      if (!editor || accountId == null) return;

      try {
        const uploaded = await uploadFiles(Array.from(files), accountId);

        uploaded.filter(hasUrl).forEach((att) => {
          const type = getAttachmentTypeByUrl(att.url) ?? 'file';
          
          editor.dispatchCommand(INSERT_ATTACHMENT_COMMAND, {
            id: att.id,
            url: att.url,
            name: att.name,
            type,
          });
        });
      } catch {
        NotificationManager.warning({ message: UPLOAD_ERROR_MESSAGE_KEY });
      } finally {
        e.target.value = '';
      }
    },
    [editorRef, accountId],
  );
}

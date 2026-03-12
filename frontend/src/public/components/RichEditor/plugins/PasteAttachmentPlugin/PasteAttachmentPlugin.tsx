import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { COMMAND_PRIORITY_EDITOR, PASTE_COMMAND } from 'lexical';
import { getFilesFromClipboard } from './getFilesFromClipboard';

export interface IPasteAttachmentPluginProps {
  onPasteFiles: (files: File[]) => Promise<void>;
}

export function PasteAttachmentPlugin({
  onPasteFiles,
}: IPasteAttachmentPluginProps): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand<ClipboardEvent>(
      PASTE_COMMAND,
      (event) => {
        const files = getFilesFromClipboard(event);
        if (files.length === 0) return false;

        onPasteFiles(files).catch(() => undefined);
        return true;
      },
      COMMAND_PRIORITY_EDITOR,
    );
  }, [editor, onPasteFiles]);

  return null;
}

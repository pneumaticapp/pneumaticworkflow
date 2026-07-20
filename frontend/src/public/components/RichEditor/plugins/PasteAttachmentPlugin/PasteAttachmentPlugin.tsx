import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { COMMAND_PRIORITY_HIGH, PASTE_COMMAND } from 'lexical';
import { getFilesFromClipboard } from './getFilesFromClipboard';

export interface IPasteAttachmentPluginProps {
  onPasteFiles: (files: File[]) => Promise<void>;
}

/**
 * Handles file paste (e.g. screenshots) before Lexical's default PASTE_COMMAND
 * handler (COMMAND_PRIORITY_EDITOR), which otherwise swallows files via
 * unused DRAG_DROP_PASTE or falls through to HTML paste when text types exist.
 */
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

        event.preventDefault();
        onPasteFiles(files).catch(() => undefined);
        return true;
      },
      COMMAND_PRIORITY_HIGH,
    );
  }, [editor, onPasteFiles]);

  return null;
}

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection, COMMAND_PRIORITY_EDITOR } from 'lexical';
import { $insertNodeToNearestRoot } from '@lexical/utils';
import {
  $createImageAttachmentNode,
  $createVideoAttachmentNode,
  $createFileAttachmentNode,
  ImageAttachmentNode,
  VideoAttachmentNode,
  FileAttachmentNode,
} from '../../nodes/attachments';
import { INSERT_ATTACHMENT_COMMAND } from './insertAttachmentCommand';

export function InsertAttachmentPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (
      !editor.hasNodes([
        ImageAttachmentNode,
        VideoAttachmentNode,
        FileAttachmentNode,
      ])
    ) {
      throw new Error(
        'InsertAttachmentPlugin: ImageAttachmentNode, VideoAttachmentNode, FileAttachmentNode must be registered',
      );
    }

    return editor.registerCommand(
      INSERT_ATTACHMENT_COMMAND,
      (payload) => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) {
          return false;
        }
        let node;
        if (payload.type === 'image') {
          node = $createImageAttachmentNode(payload);
        } else if (payload.type === 'video') {
          node = $createVideoAttachmentNode(payload);
        } else {
          node = $createFileAttachmentNode(payload);
        }
        $insertNodeToNearestRoot(node);
        return true;
      },
      COMMAND_PRIORITY_EDITOR,
    );
  }, [editor]);

  return null;
}

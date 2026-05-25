import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  $isRootNode,
  $createParagraphNode,
  COMMAND_PRIORITY_EDITOR,
  type LexicalNode,
} from 'lexical';
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

/**
 * Moves a block-level decorator out of a ParagraphNode to root level.
 * Handles text splitting: nodes after the decorator go into a new paragraph.
 */
function $promoteBlockDecorator(node: LexicalNode): void {
  const parent = node.getParent();
  if (parent == null || $isRootNode(parent)) return;

  const nodesAfter = node.getNextSiblings();
  parent.insertAfter(node);

  if (nodesAfter.length > 0) {
    const newParagraph = $createParagraphNode();
    node.insertAfter(newParagraph);
    nodesAfter.forEach((n) => newParagraph.append(n));
  }

  if (parent.getChildrenSize() === 0) {
    parent.remove();
  }
}

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

    const removeInsert = editor.registerCommand(
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

    const removeImageTransform = editor.registerNodeTransform(
      ImageAttachmentNode,
      $promoteBlockDecorator,
    );
    const removeVideoTransform = editor.registerNodeTransform(
      VideoAttachmentNode,
      $promoteBlockDecorator,
    );
    const removeFileTransform = editor.registerNodeTransform(
      FileAttachmentNode,
      $promoteBlockDecorator,
    );

    return () => {
      removeInsert();
      removeImageTransform();
      removeVideoTransform();
      removeFileTransform();
    };
  }, [editor]);

  return null;
}

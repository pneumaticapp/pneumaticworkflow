import { useEffect } from 'react';
import {
  $getSelection,
  $isNodeSelection,
  $isDecoratorNode,
  KEY_ARROW_DOWN_COMMAND,
  KEY_ARROW_UP_COMMAND,
  COMMAND_PRIORITY_LOW,
  type LexicalNode,
} from 'lexical';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

function $isBlockDecorator(node: LexicalNode | null | undefined): boolean {
  return node != null && $isDecoratorNode(node) && !node.isInline();
}

function $skipForward(startNode: LexicalNode): boolean {
  let target: LexicalNode | null = startNode.getNextSibling();
  while (target != null && $isBlockDecorator(target)) {
    target = target.getNextSibling();
  }
  if (target != null) {
    target.selectStart();
    return true;
  }
  return false;
}

function $skipBackward(startNode: LexicalNode | null): boolean {
  let target: LexicalNode | null = startNode?.getPreviousSibling() ?? null;
  while (target != null && $isBlockDecorator(target)) {
    target = target.getPreviousSibling();
  }
  if (target != null) {
    target.selectEnd();
    return true;
  }
  return false;
}

/**
 * Skips block-level decorator nodes (images, videos, files) during
 * vertical arrow-key navigation so the cursor never "disappears" inside them.
 */
export function DecoratorNavigationPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    let pendingDirection: 'up' | 'down' | null = null;

    const removeDown = editor.registerCommand(
      KEY_ARROW_DOWN_COMMAND,
      () => {
        const selection = $getSelection();

        if ($isNodeSelection(selection)) {
          const nodes = selection.getNodes();
          if (nodes.length === 1 && $isBlockDecorator(nodes[0])) {
            return $skipForward(nodes[0]);
          }
        }

        pendingDirection = 'down';
        return false;
      },
      COMMAND_PRIORITY_LOW,
    );

    const removeUp = editor.registerCommand(
      KEY_ARROW_UP_COMMAND,
      () => {
        const selection = $getSelection();

        if ($isNodeSelection(selection)) {
          const nodes = selection.getNodes();
          if (nodes.length === 1 && $isBlockDecorator(nodes[0])) {
            return $skipBackward(nodes[0]);
          }
        }

        pendingDirection = 'up';
        return false;
      },
      COMMAND_PRIORITY_LOW,
    );

    const removeUpdateListener = editor.registerUpdateListener(() => {
      if (pendingDirection == null) return;
      const direction = pendingDirection;
      pendingDirection = null;

      editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isNodeSelection(selection)) return;

        const nodes = selection.getNodes();
        if (nodes.length !== 1 || !$isBlockDecorator(nodes[0])) return;

        const node = nodes[0];
        editor.update(() => {
          if (direction === 'down') {
            if (!$skipForward(node)) $skipBackward(node);
          } else if (!$skipBackward(node)) $skipForward(node);
        });
      });
    });

    return () => {
      removeDown();
      removeUp();
      removeUpdateListener();
    };
  }, [editor]);

  return null;
}

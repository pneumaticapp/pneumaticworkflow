import { useEffect } from 'react';
import {
  $getSelection,
  $isNodeSelection,
  $isRangeSelection,
  $isDecoratorNode,
  $createNodeSelection,
  $setSelection,
  KEY_ARROW_DOWN_COMMAND,
  KEY_ARROW_UP_COMMAND,
  KEY_BACKSPACE_COMMAND,
  KEY_DELETE_COMMAND,
  CUT_COMMAND,
  COPY_COMMAND,
  COMMAND_PRIORITY_LOW,
  COMMAND_PRIORITY_CRITICAL,
  type LexicalNode,
} from 'lexical';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

function $isBlockDecorator(node: LexicalNode | null | undefined): boolean {
  return node != null && $isDecoratorNode(node) && !node.isInline();
}

function $selectNode(node: LexicalNode): void {
  const selection = $createNodeSelection();
  selection.add(node.getKey());
  $setSelection(selection);
}

function $navigateForward(startNode: LexicalNode): boolean {
  const target = startNode.getNextSibling();
  if (target == null) return false;

  if ($isBlockDecorator(target)) {
    $selectNode(target);
    return true;
  }

  target.selectStart();
  return true;
}

function $navigateBackward(startNode: LexicalNode): boolean {
  const target = startNode.getPreviousSibling();
  if (target == null) return false;

  if ($isBlockDecorator(target)) {
    $selectNode(target);
    return true;
  }

  target.selectEnd();
  return true;
}

function $skipAllDecoratorsBackward(startNode: LexicalNode): boolean {
  let target: LexicalNode | null = startNode.getPreviousSibling();
  while (target != null && $isBlockDecorator(target)) {
    target = target.getPreviousSibling();
  }
  if (target != null) {
    target.selectEnd();
    return true;
  }

  target = startNode.getNextSibling();
  while (target != null && $isBlockDecorator(target)) {
    target = target.getNextSibling();
  }
  if (target != null) {
    target.selectStart();
    return true;
  }
  return false;
}

function $skipAllDecoratorsForward(startNode: LexicalNode): boolean {
  let target: LexicalNode | null = startNode.getNextSibling();
  while (target != null && $isBlockDecorator(target)) {
    target = target.getNextSibling();
  }
  if (target != null) {
    target.selectStart();
    return true;
  }

  target = startNode.getPreviousSibling();
  while (target != null && $isBlockDecorator(target)) {
    target = target.getPreviousSibling();
  }
  if (target != null) {
    target.selectEnd();
    return true;
  }
  return false;
}

function $getSelectedBlockDecorator(): LexicalNode | null {
  const selection = $getSelection();
  if (!$isNodeSelection(selection)) return null;

  const nodes = selection.getNodes();
  if (nodes.length > 0 && nodes.some((node) => $isBlockDecorator(node))) {
    return nodes[0];
  }
  return null;
}

function $isAtBlockStart(): LexicalNode | null {
  const selection = $getSelection();
  if (!$isRangeSelection(selection) || !selection.isCollapsed()) return null;

  const { anchor } = selection;
  if (anchor.offset !== 0) return null;

  const anchorNode = anchor.getNode();
  const topElement = anchorNode.getTopLevelElement();
  if (topElement == null) return null;

  if (anchorNode === topElement) return topElement;
  if (anchorNode === topElement.getFirstDescendant()) return topElement;

  return null;
}

function $isAtBlockEnd(): LexicalNode | null {
  const selection = $getSelection();
  if (!$isRangeSelection(selection) || !selection.isCollapsed()) return null;

  const { anchor } = selection;
  const anchorNode = anchor.getNode();
  const topElement = anchorNode.getTopLevelElement();
  if (topElement == null) return null;

  if (anchorNode === topElement) {
    return anchor.offset === topElement.getChildrenSize() ? topElement : null;
  }

  if (
    anchorNode === topElement.getLastDescendant() &&
    anchor.offset === anchorNode.getTextContentSize()
  ) {
    return topElement;
  }

  return null;
}

/**
 * Handles keyboard navigation around block-level decorator nodes
 * (images, videos, files). When the cursor lands on a decorator it stays
 * selected (NodeSelection) instead of being skipped over. Backspace and
 * Delete jump past the decorator to the nearest text position (both from
 * NodeSelection and from RangeSelection at a block edge). Cut copies
 * without removing. Attachments can only be deleted via their own X button.
 */
export function DecoratorNavigationPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const removeDown = editor.registerCommand(
      KEY_ARROW_DOWN_COMMAND,
      () => {
        const selection = $getSelection();
        if ($isNodeSelection(selection)) {
          const nodes = selection.getNodes();
          if (nodes.length === 1 && $isBlockDecorator(nodes[0])) {
            return $navigateForward(nodes[0]);
          }
        }
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
            return $navigateBackward(nodes[0]);
          }
        }
        return false;
      },
      COMMAND_PRIORITY_LOW,
    );

    const removeBackspace = editor.registerCommand(
      KEY_BACKSPACE_COMMAND,
      () => {
        const decoratorNode = $getSelectedBlockDecorator();
        if (decoratorNode != null) {
          $skipAllDecoratorsBackward(decoratorNode);
          return true;
        }

        const block = $isAtBlockStart();
        if (block == null) return false;

        const prev = block.getPreviousSibling();
        if (prev == null || !$isBlockDecorator(prev)) return false;

        $skipAllDecoratorsBackward(prev);
        if (block.getTextContentSize() === 0) {
          block.remove();
        }
        return true;
      },
      COMMAND_PRIORITY_CRITICAL,
    );

    const removeDelete = editor.registerCommand(
      KEY_DELETE_COMMAND,
      () => {
        const decoratorNode = $getSelectedBlockDecorator();
        if (decoratorNode != null) {
          $skipAllDecoratorsForward(decoratorNode);
          return true;
        }

        const block = $isAtBlockEnd();
        if (block == null) return false;

        const next = block.getNextSibling();
        if (next == null || !$isBlockDecorator(next)) return false;

        $skipAllDecoratorsForward(next);
        if (block.getTextContentSize() === 0) {
          block.remove();
        }
        return true;
      },
      COMMAND_PRIORITY_CRITICAL,
    );

    const removeCut = editor.registerCommand<ClipboardEvent | null>(
      CUT_COMMAND,
      (event) => {
        if ($getSelectedBlockDecorator() == null) return false;

        if (event != null) {
          editor.dispatchCommand(COPY_COMMAND, event);
        }
        return true;
      },
      COMMAND_PRIORITY_CRITICAL,
    );

    return () => {
      removeDown();
      removeUp();
      removeBackspace();
      removeDelete();
      removeCut();
    };
  }, [editor]);

  return null;
}

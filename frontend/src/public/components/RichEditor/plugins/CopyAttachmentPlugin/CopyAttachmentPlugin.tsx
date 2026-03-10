import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  COPY_COMMAND,
  CUT_COMMAND,
  COMMAND_PRIORITY_HIGH,
  $getSelection,
  $isRangeSelection,
  $isDecoratorNode,
  $createNodeSelection,
} from 'lexical';
import {
  $getClipboardDataFromSelection,
  setLexicalClipboardDataTransfer,
} from '@lexical/clipboard';

/**
 * Builds expanded clipboard data when selection contains decorator nodes.
 * Must run in a Lexical update context (COPY/CUT handlers are already invoked
 * inside editor.update()), because $getClipboardDataFromSelection clones nodes
 * for HTML export and Lexical throws in read-only mode.
 */
function $buildExpandedClipboardData(
  event: ClipboardEvent,
): boolean {
  const { clipboardData } = event;
  if (clipboardData == null) return false;

  const selection = $getSelection();
  if (!$isRangeSelection(selection) || selection.isCollapsed()) {
    return false;
  }

  const anchorNode = selection.anchor.getNode();
  const focusNode = selection.focus.getNode();
  const fullNodes = anchorNode.getNodesBetween(focusNode);

  const hasDecorator = fullNodes.some((node) => $isDecoratorNode(node));
  if (!hasDecorator) return false;

  const expandedSelection = $createNodeSelection();
  fullNodes.forEach((node) => expandedSelection.add(node.getKey()));

  const data = $getClipboardDataFromSelection(expandedSelection);
  event.preventDefault();
  setLexicalClipboardDataTransfer(clipboardData, data);
  return true;
}

/**
 * Ensures images, video and other decorator nodes are included when copying
 * or cutting a selection. In Safari the DOM selection may skip decorator
 * elements so RangeSelection.getNodes() can miss them. The COPY/CUT command
 * is already run inside editor.update(), so we use getNodesBetween() to
 * collect all nodes—including decorators—then write the expanded data to
 * clipboard (node cloning for HTML export requires a writable context).
 */
export function CopyAttachmentPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const handleClipboard = (event: ClipboardEvent | null): boolean => {
      if (event == null || !('clipboardData' in event)) {
        return false;
      }
      return $buildExpandedClipboardData(event);
    };

    const removeCopy = editor.registerCommand<ClipboardEvent | null>(
      COPY_COMMAND,
      handleClipboard,
      COMMAND_PRIORITY_HIGH,
    );

    const removeCut = editor.registerCommand<ClipboardEvent | null>(
      CUT_COMMAND,
      (event) => {
        const copyHandled = handleClipboard(event);
        if (copyHandled) {
          editor.update(() => {
            const selection = $getSelection();
            if (!$isRangeSelection(selection) || selection.isCollapsed()) return;
            const anchorNode = selection.anchor.getNode();
            const focusNode = selection.focus.getNode();
            const fullNodes = anchorNode.getNodesBetween(focusNode);
            fullNodes.forEach((node) => node.remove());
          });
        }
        return copyHandled;
      },
      COMMAND_PRIORITY_HIGH,
    );

    return () => {
      removeCopy();
      removeCut();
    };
  }, [editor]);

  return null;
}

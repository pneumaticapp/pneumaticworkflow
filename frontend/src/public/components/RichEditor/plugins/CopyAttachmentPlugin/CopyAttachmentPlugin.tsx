import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  COPY_COMMAND,
  COMMAND_PRIORITY_HIGH,
  $getSelection,
  $isRangeSelection,
  $createNodeSelection,
} from 'lexical';
import {
  $getClipboardDataFromSelection,
  setLexicalClipboardDataTransfer,
} from '@lexical/clipboard';

/**
 * Ensures images, video and other decorator nodes are included when copying
 * a selection. In some browsers (e.g. Safari) DOM selection may not include
 * decorator elements, so RangeSelection.getNodes() can miss them. We rebuild
 * clipboard data from anchor.getNode().getNodesBetween(focus.getNode()) so
 * all nodes in the range are copied.
 */
export function CopyAttachmentPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand<ClipboardEvent | null>(
      COPY_COMMAND,
      (event) => {
        if (event == null || !(event instanceof ClipboardEvent)) {
          return false;
        }
        const {clipboardData} = event;
        if (clipboardData == null) {
          return false;
        }

        let handled = false;
        editor.update(() => {
          const selection = $getSelection();
          if (
            !$isRangeSelection(selection) ||
            selection.isCollapsed()
          ) {
            return;
          }
          const anchorNode = selection.anchor.getNode();
          const focusNode = selection.focus.getNode();
          const fullNodes = anchorNode.getNodesBetween(focusNode);
          if (fullNodes.length === 0) {
            return;
          }
          const expandedSelection = $createNodeSelection();
          fullNodes.forEach((node) => {
            expandedSelection.add(node.getKey());
          });
          const data = $getClipboardDataFromSelection(expandedSelection);
          event.preventDefault();
          setLexicalClipboardDataTransfer(clipboardData, data);
          handled = true;
        });

        return handled;
      },
      COMMAND_PRIORITY_HIGH,
    );
  }, [editor]);

  return null;
}

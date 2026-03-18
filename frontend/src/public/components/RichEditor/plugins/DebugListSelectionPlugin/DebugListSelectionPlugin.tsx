import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection } from 'lexical';
import { $getNearestNodeOfType } from '@lexical/utils';
import { ListItemNode } from '@lexical/list';

const DEBUG_LOG_ENDPOINT = 'http://127.0.0.1:7243/ingest/508f3e25-176b-49b9-b4ee-787ecc748fdd';

export function DebugListSelectionPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection) || !selection.isCollapsed()) return;
        const anchorNode = selection.anchor.getNode();
        const listItem = $getNearestNodeOfType(anchorNode, ListItemNode);
        if (!listItem) return;

        const anchorOffset = selection.anchor.offset;
        const anchorType = anchorNode.getType();
        const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent) || /iPad|iPhone|Mac/.test(navigator.userAgent);

        // #region agent log
        fetch(DEBUG_LOG_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'DebugListSelectionPlugin.tsx:selection-in-list',
            message: 'Selection inside list item',
            data: {
              isSafari,
              anchorNodeType: anchorType,
              anchorOffset,
              listItemKey: listItem.getKey(),
              isAtStart: anchorOffset === 0,
            },
            timestamp: Date.now(),
            hypothesisId: anchorOffset === 0 ? 'H1_H3' : 'H2',
          }),
        }).catch(() => {});
        // #endregion
      });
    });
  }, [editor]);

  return null;
}

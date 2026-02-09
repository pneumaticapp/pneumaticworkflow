import { useCallback, useEffect, useState } from 'react';
import { $getSelection, $isRangeSelection } from 'lexical';
import { $getNearestNodeOfType } from '@lexical/utils';
import { ListNode } from '@lexical/list';
import { LinkNode } from '@lexical/link';
import type { LexicalEditor } from 'lexical';
import type { IToolbarState, TListType } from './types';

const EMPTY_STATE: IToolbarState = {
  isBold: false,
  isItalic: false,
  listType: null,
  isLink: false,
};

function listTypeFromNode(listNode: ListNode): TListType {
  const type = listNode.getListType();
  if (type === 'number') return 'number';
  if (type === 'bullet') return 'bullet';
  return null;
}

function useToolbarState(editor: LexicalEditor): IToolbarState {
  const [state, setState] = useState<IToolbarState>(EMPTY_STATE);

  const syncSelectionState = useCallback(() => {
    editor.getEditorState().read(() => {
      const selection = $getSelection();

      if (!$isRangeSelection(selection)) {
        setState(EMPTY_STATE);
        return;
      }

      const anchorNode = selection.anchor.getNode();
      const listNode = $getNearestNodeOfType(anchorNode, ListNode);
      const linkNode = $getNearestNodeOfType(anchorNode, LinkNode);

      setState({
        isBold: selection.hasFormat('bold'),
        isItalic: selection.hasFormat('italic'),
        listType: listNode ? listTypeFromNode(listNode) : null,
        isLink: linkNode !== null,
      });
    });
  }, [editor]);

  useEffect(() => {
    const unregisterUpdate = editor.registerUpdateListener(syncSelectionState);
    const unregisterRoot = editor.registerRootListener(syncSelectionState);
    return () => {
      unregisterUpdate();
      unregisterRoot();
    };
  }, [editor, syncSelectionState]);

  return state;
}

export { useToolbarState };

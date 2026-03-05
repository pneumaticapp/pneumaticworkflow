import type { LexicalEditor } from 'lexical';
import { $getNodeByKey, $getSelection, $isRangeSelection } from 'lexical';
import { $isListNode } from '@lexical/list';
import {
  applyBackspaceOnEmptyChecklist,
  applySplitChecklistEnter,
  assignNewChecklistIds,
  convertBlockToChecklist,
  convertChecklistItemToParagraph,
  convertChecklistToList,
  convertListToChecklist,
  getBackspaceOnEmptyChecklistPayload,
  getBlockNodeFromSelection,
  getChecklistItemNodeFromSelection,
  insertChecklistAndSelectFirst,
  isCursorAtStartOfChecklistItem,
  nodesContainChecklist,
  removeDuplicateClipboardParagraphs,
  selectStartOfChecklistItem,
} from './checklistPluginUtils';
import {
  $createChecklistNode,
  $createChecklistItemNode,
  $isChecklistNode,
  $isChecklistItemNode,
} from '../../nodes';
import { createChecklistApiName, createChecklistSelectionApiName } from '../../../../utils/createId';



export function createEnterKeyHandler(editor: LexicalEditor) {
  return (event: KeyboardEvent | null): boolean => {
    const emptyPayload = editor.getEditorState().read(() => getBackspaceOnEmptyChecklistPayload());
    if (emptyPayload !== null) {
      event?.preventDefault();
      editor.update(() => applyBackspaceOnEmptyChecklist(emptyPayload));
      requestAnimationFrame(() => editor.focus());
      return true;
    }
    const checklistKey = editor.getEditorState().read(() => {
      const node = getChecklistItemNodeFromSelection();
      return node?.getKey() ?? null;
    });
    if (checklistKey == null) return false;
    event?.preventDefault();
    editor.update(() => applySplitChecklistEnter());
    requestAnimationFrame(() => editor.focus());
    return true;
  };
}

export function createInsertChecklistHandler(editor: LexicalEditor) {
  return (): boolean => {
    editor.update(() => {
      const selection = $getSelection();
      if (!$isRangeSelection(selection)) return;

      const currentItem = getChecklistItemNodeFromSelection();
      if (currentItem) {
        convertChecklistItemToParagraph(currentItem);
        return;
      }

      const block = getBlockNodeFromSelection();
      if (
        block !== null &&
        !$isChecklistNode(block) &&
        !$isChecklistItemNode(block) &&
        !$isListNode(block)
      ) {
        const newItem = convertBlockToChecklist(block);
        if (newItem !== null) {
          selectStartOfChecklistItem(newItem);
          return;
        }
      }
      if (block !== null && $isListNode(block)) {
        const newItem = convertListToChecklist(block);
        if (newItem !== null) {
          selectStartOfChecklistItem(newItem);
          return;
        }
      }
      const listApiName = createChecklistApiName();
      const checklistRoot = $createChecklistNode({ listApiName });
      const firstItem = $createChecklistItemNode({
        listApiName,
        itemApiName: createChecklistSelectionApiName(),
      });
      insertChecklistAndSelectFirst(checklistRoot, firstItem);
    });
    requestAnimationFrame(() => editor.focus());
    return true;
  };
}

export function createBackspaceHandler(editor: LexicalEditor) {
  return (event: KeyboardEvent): boolean => {
    const emptyPayload = editor.getEditorState().read(() => getBackspaceOnEmptyChecklistPayload());
    if (emptyPayload != null) {
      event.preventDefault();
      editor.update(() => applyBackspaceOnEmptyChecklist(emptyPayload));
      return true;
    }

    const itemKey = editor.getEditorState().read(() => isCursorAtStartOfChecklistItem());
    if (itemKey != null) {
      event.preventDefault();
      editor.update(() => {
        const item = $getNodeByKey(itemKey);
        if (item && $isChecklistItemNode(item)) {
          convertChecklistItemToParagraph(item);
        }
      });
      return true;
    }

    return false;
  };
}

/** On paste: assign new ids to checklists/items and remove trailing empty paragraph. */
export function createPasteClipboardNodesHandler() {
  return (payload: { nodes: import('lexical').LexicalNode[]; selection: import('lexical').BaseSelection }): boolean => {
    const hasChecklist = nodesContainChecklist(payload.nodes);
    if (hasChecklist) assignNewChecklistIds(payload.nodes);
    const filtered = removeDuplicateClipboardParagraphs(payload.nodes);
    const changed =
      hasChecklist ||
      filtered.length !== payload.nodes.length ||
      filtered.some((n, i) => n !== payload.nodes[i]);
    if (!changed) return false;
    payload.selection.insertNodes(filtered);
    return true;
  };
}

export function createConvertChecklistToListHandler(editor: LexicalEditor) {
  return (listType: 'number' | 'bullet'): boolean => {
    const handled = editor.getEditorState().read(() => {
      const item = getChecklistItemNodeFromSelection();
      if (!item) return false;
      const parent = item.getParent();
      if (!parent || !$isChecklistNode(parent)) return false;
      return true;
    });
    if (!handled) return false;
    editor.update(() => {
      const item = getChecklistItemNodeFromSelection();
      if (!item) return;
      const parent = item.getParent();
      if (!parent || !$isChecklistNode(parent)) return;
      convertChecklistToList(parent, listType);
    });
    requestAnimationFrame(() => editor.focus());
    return true;
  };
}
import type { LexicalEditor } from 'lexical';
import { $getNodeByKey, $getSelection, $isRangeSelection } from 'lexical';
import { $isListNode } from '@lexical/list';
import {
  applyBackspaceOnEmptyChecklist,
  applyInsertParagraphFromEmptyChecklist,
  assignNewChecklistIds,
  convertBlockToChecklist,
  getBackspaceOnEmptyChecklistPayload,
  getBlockNodeFromSelection,
  getChecklistItemNodeFromSelection,
  getInsertParagraphFromEmptyChecklistPayload,
  insertChecklistAndSelectFirst,
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
import { createChecklistApiName, createChecklistSelectionApiName } from '../../../../../utils/createId';



export function createEnterKeyHandler(editor: LexicalEditor) {
  return (event: KeyboardEvent | null): boolean => {
    const paragraphPayload = editor.getEditorState().read(() =>
      getInsertParagraphFromEmptyChecklistPayload(),
    );
    if (paragraphPayload !== null) {
      event?.preventDefault();
      editor.update(() => applyInsertParagraphFromEmptyChecklist(paragraphPayload));
      requestAnimationFrame(() => editor.focus());
      return true;
    }
    const checklistKey = editor.getEditorState().read(() => {
      const node = getChecklistItemNodeFromSelection();
      return node?.getKey() ?? null;
    });
    if (checklistKey == null) return false;
    event?.preventDefault();
    editor.update(() => {
      const current = $getNodeByKey(checklistKey);
      if (!current || !$isChecklistItemNode(current)) return;
      const writable = current.getWritable();
      const parent = writable.getParent();
      const listApiName =
        parent != null && $isChecklistNode(parent)
          ? parent.getListApiName()
          : writable.getListApiName();
      const newNode = $createChecklistItemNode({
        listApiName,
        itemApiName: createChecklistSelectionApiName(),
      });
      writable.insertAfter(newNode);
      selectStartOfChecklistItem(newNode);
    });
    requestAnimationFrame(() => editor.focus());
    return true;
  };
}

export function createInsertChecklistHandler(editor: LexicalEditor) {
  return (): boolean => {
    editor.update(() => {
      const selection = $getSelection();
      if (!$isRangeSelection(selection)) return;
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
  return (): boolean => {
    const payload = editor.getEditorState().read(() => getBackspaceOnEmptyChecklistPayload());
    if (payload == null) return false;
    editor.update(() => applyBackspaceOnEmptyChecklist(payload));
    return true;
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
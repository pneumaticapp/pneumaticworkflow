import type { ElementNode, LexicalNode } from 'lexical';
import {
  $createParagraphNode,
  $getNodeByKey,
  $getSelection,
  $insertNodes,
  $isElementNode,
  $isParagraphNode,
  $isRangeSelection,
  $isRootOrShadowRoot,
  $isTextNode,
  $setSelection,
} from 'lexical';

import {
  ChecklistNode,
  ChecklistItemNode,
  $createChecklistNode,
  $createChecklistItemNode,
  $isChecklistNode,
  $isChecklistItemNode,
} from '../../nodes';
import { createChecklistApiName, createChecklistSelectionApiName } from '../../../../utils/createId';
import type {
  InsertParagraphFromEmptyChecklistPayload,
  BackspaceOnEmptyChecklistPayload,
} from './types';

/** Normalize for dedup: trim + collapse spaces/newlines. */
function normalizeTextForDedup(text: string): string {
  return text.trim().replace(/\s+/g, ' ');
}

function filterUniqueByKey<T>(items: T[], getKey: (item: T) => string | null): T[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = getKey(item);
    if (key === null) return true;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function getListApiNameFromSiblings(prev: LexicalNode | null, next: LexicalNode | null): string {
  if (prev && $isChecklistNode(prev)) return prev.getListApiName();
  if (next && $isChecklistNode(next)) return next.getListApiName();
  return createChecklistApiName();
}

function addParagraphTextsFromChecklistItem(item: ChecklistItemNode, set: Set<string>): void {
  item.getChildren().forEach((desc) => {
    if ($isParagraphNode(desc)) {
      const t = normalizeTextForDedup(desc.getTextContent());
      if (t.length > 0) set.add(t);
    }
  });
}

function getParagraphTextsInsideChecklistItems(nodes: LexicalNode[]): Set<string> {
  const set = new Set<string>();
  nodes.forEach((node) => {
    if ($isChecklistNode(node)) {
      node.getChildren().forEach((child) => {
        if ($isChecklistItemNode(child)) addParagraphTextsFromChecklistItem(child as ChecklistItemNode, set);
      });
    } else if ($isChecklistItemNode(node)) {
      addParagraphTextsFromChecklistItem(node as ChecklistItemNode, set);
    } else if ($isElementNode(node)) {
      getParagraphTextsInsideChecklistItems(node.getChildren()).forEach((t) => set.add(t));
    }
  });
  return set;
}

function getLexicalChecklistContentKey(node: LexicalNode): string | null {
  if (!$isChecklistNode(node)) return null;
  const itemTexts = (node as ChecklistNode)
    .getChildren()
    .filter((c): c is ChecklistItemNode => $isChecklistItemNode(c))
    .map((c) => normalizeTextForDedup(c.getTextContent()));
  return JSON.stringify(itemTexts);
}

function shouldDropClipboardNode(
  node: LexicalNode,
  index: number,
  checklistTexts: Set<string>,
  hasChecklist: boolean,
  checklistIdx: number,
): boolean {
  if (!$isParagraphNode(node)) return false;
  const text = normalizeTextForDedup(node.getTextContent());
  const afterChecklist = hasChecklist && checklistIdx >= 0 && index === checklistIdx + 1;
  return (afterChecklist && (text.length === 0 || checklistTexts.has(text))) || (text.length > 0 && checklistTexts.has(text));
}

/** On paste: drop only the trailing empty paragraph after checklist and duplicate paragraph texts. */
export function removeDuplicateClipboardParagraphs(nodes: LexicalNode[]): LexicalNode[] {
  const checklistTexts = getParagraphTextsInsideChecklistItems(nodes);
  const hasChecklist = nodes.some((n) => $isChecklistNode(n));
  const checklistIdx = nodes.findIndex((n) => $isChecklistNode(n));
  const filtered = nodes.filter(
    (node, index) => !shouldDropClipboardNode(node, index, checklistTexts, hasChecklist, checklistIdx),
  );
  return filterUniqueByKey(filtered, getLexicalChecklistContentKey);
}

export function nodesContainChecklist(nodes: LexicalNode[]): boolean {
  for (let i = 0; i < nodes.length; i += 1) {
    const node = nodes[i];
    if ($isChecklistNode(node) || $isChecklistItemNode(node)) return true;
    if ($isElementNode(node)) {
      if (nodesContainChecklist(node.getChildren())) return true;
    }
  }
  return false;
}

export function assignNewChecklistIds(nodes: LexicalNode[]): void {
  nodes.forEach((node) => {
    if ($isChecklistNode(node)) {
      const listNode = node as ChecklistNode;
      const newId = createChecklistApiName();
      /* eslint-disable no-underscore-dangle -- clipboard nodes not in editor state yet */
      (listNode as { __listApiName: string }).__listApiName = newId;
      listNode.getChildren().forEach((child: LexicalNode) => {
        if ($isChecklistItemNode(child)) {
          const item = child as ChecklistItemNode;
          (item as { __listApiName: string }).__listApiName = newId;
          (item as { __itemApiName: string }).__itemApiName = createChecklistSelectionApiName();
        }
      });
      /* eslint-enable no-underscore-dangle */
    } else if ($isElementNode(node)) assignNewChecklistIds(node.getChildren());
  });
}

export function getChecklistItemNodeFromSelection(): ChecklistItemNode | null {
  const sel = $getSelection();
  if (!sel || !$isRangeSelection(sel)) return null;
  let n: LexicalNode | null = sel.anchor.getNode();
  while (n) {
    if ($isChecklistItemNode(n)) return n as ChecklistItemNode;
    n = n.getParent();
  }
  return null;
}

export function isChecklistItemEmpty(itemNode: ChecklistItemNode): boolean {
  return itemNode.getTextContentSize() === 0 || itemNode.getTextContent().trim() === '';
}

export function getInsertParagraphFromEmptyChecklistPayload(): InsertParagraphFromEmptyChecklistPayload | null {
  const sel = $getSelection();
  if (!sel || !$isRangeSelection(sel) || !sel.isCollapsed()) return null;
  const item = getChecklistItemNodeFromSelection();
  if (!item || !isChecklistItemEmpty(item)) return null;
  const parent = item.getParent();
  if (!parent || !$isChecklistNode(parent)) return null;
  return { itemKey: item.getKey(), parentKey: parent.getKey(), nextSiblingKeys: item.getNextSiblings().map((s) => s.getKey()) };
}

export function applyInsertParagraphFromEmptyChecklist(
  payload: InsertParagraphFromEmptyChecklistPayload,
): void {
  const item = $getNodeByKey(payload.itemKey);
  const parent = $getNodeByKey(payload.parentKey);
  if (!item || !$isChecklistItemNode(item) || !parent || !$isChecklistNode(parent)) return;
  const nextSiblings = payload.nextSiblingKeys
    .map((key) => $getNodeByKey(key))
    .filter((n): n is ChecklistItemNode => n !== null && $isChecklistItemNode(n));
  const checklistWritable = parent.getWritable();
  const paragraph = $createParagraphNode();
  checklistWritable.insertAfter(paragraph);
  if (nextSiblings.length > 0) {
    const newChecklist = $createChecklistNode({ listApiName: createChecklistApiName() });
    paragraph.insertAfter(newChecklist);
    nextSiblings.forEach((sibling) => {
      sibling.remove();
      newChecklist.append(sibling);
    });
  }
  item.remove();
  if (checklistWritable.getChildrenSize() === 0) {
    checklistWritable.remove();
  }
  paragraph.selectStart();
}

export function getBlockNodeFromSelection(): ElementNode | null {
  const sel = $getSelection();
  if (!sel || !$isRangeSelection(sel)) return null;
  let n: LexicalNode | null = sel.anchor.getNode();
  while (n) {
    const parent: LexicalNode | null = n.getParent();
    if (parent && $isRootOrShadowRoot(parent) && $isElementNode(n)) return n as ElementNode;
    n = parent;
  }
  return null;
}

export function convertBlockToChecklist(block: ElementNode): ChecklistItemNode | null {
  if ($isChecklistNode(block) || $isChecklistItemNode(block)) return null;
  const itemApiName = createChecklistSelectionApiName();
  const prevSibling = block.getPreviousSibling();
  const nextSibling = block.getNextSibling();
  const listApiName = getListApiNameFromSiblings(prevSibling, nextSibling);
  const firstItem = $createChecklistItemNode({
    listApiName,
    itemApiName,
  });
  firstItem.setFormat(block.getFormatType());
  firstItem.setIndent(block.getIndent());
  block.getChildren().forEach((child) => {
    firstItem.append(child);
  });
  if ($isChecklistNode(prevSibling)) {
    prevSibling.append(firstItem);
    block.remove();
    return firstItem;
  }
  if ($isChecklistNode(nextSibling)) {
    nextSibling.getFirstChildOrThrow().insertBefore(firstItem);
    block.remove();
    return firstItem;
  }
  const checklistRoot = $createChecklistNode({ listApiName });
  checklistRoot.append(firstItem);
  block.replace(checklistRoot);
  return firstItem;
}

/** Ensure checklist item has a paragraph child so cursor is visible. */
export function ensureParagraphInChecklistItem(item: ChecklistItemNode): void {
  const writable = item.getWritable();
  if (writable.getChildrenSize() === 0) {
    writable.append($createParagraphNode());
  }
}

export function selectStartOfChecklistItem(item: ChecklistItemNode): void {
  ensureParagraphInChecklistItem(item);
  const textNode = item.getFirstDescendant();
  if (textNode && $isTextNode(textNode)) {
    textNode.selectStart();
    return;
  }
  const first = item.getFirstChild();
  if (first && $isParagraphNode(first)) {
    first.selectStart();
    return;
  }
  item.selectStart();
}

export function getBackspaceOnEmptyChecklistPayload(): BackspaceOnEmptyChecklistPayload | null {
  const sel = $getSelection();
  if (!sel || !$isRangeSelection(sel) || !sel.isCollapsed()) return null;
  const item = getChecklistItemNodeFromSelection();
  if (!item || !isChecklistItemEmpty(item)) return null;
  const parent = item.getParent();
  return { itemKey: item.getKey(), parentKey: parent?.getKey() ?? null, prevItemKey: item.getPreviousSibling()?.getKey() ?? null };
}

export function applyBackspaceOnEmptyChecklist(payload: BackspaceOnEmptyChecklistPayload): void {
  const item = $getNodeByKey(payload.itemKey);
  if (!item || !$isChecklistItemNode(item)) return;
  const parent = payload.parentKey !== null ? $getNodeByKey(payload.parentKey) : null;
  const prevItem = payload.prevItemKey !== null ? $getNodeByKey(payload.prevItemKey) : null;
  item.remove();
  if (prevItem) {
    $setSelection(prevItem.selectEnd());
    return;
  }
  if (!parent || !$isChecklistNode(parent)) return;
  const writable = parent.getWritable();
  if (writable.getChildrenSize() === 0) {
    const prev = writable.getPreviousSibling();
    const grandParent = writable.getParent();
    writable.remove();
    if (prev) $setSelection(prev.selectEnd());
    else if (grandParent) $setSelection(grandParent.selectEnd());
  } else {
    $setSelection(writable.selectStart());
  }
}

export function insertChecklistAndSelectFirst(
  checklistRoot: ReturnType<typeof $createChecklistNode>,
  firstItem: ChecklistItemNode,
): void {
  checklistRoot.append(firstItem);
  $insertNodes([checklistRoot]);
  selectStartOfChecklistItem(firstItem);
}

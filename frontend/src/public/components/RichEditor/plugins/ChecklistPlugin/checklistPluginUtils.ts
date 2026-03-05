import type { ElementNode, LexicalNode } from 'lexical';
import {
  $createParagraphNode,
  $getNodeByKey,
  $getRoot,
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
  $createListItemNode as $createLexicalListItemNode,
  $createListNode as $createLexicalListNode,
  $isListItemNode as $isLexicalListItemNode,
  $isListNode as $isLexicalListNode,
} from '@lexical/list';

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

/**
 * Returns root-level block nodes (direct children of root) that intersect the current selection.
 * Order matches document order.
 */
export function getSelectedRootBlocks(): ElementNode[] {
  const selection = $getSelection();
  if (!selection || !$isRangeSelection(selection)) return [];
  const blockKeys = new Set<string>();
  selection.getNodes().forEach((node) => {
    let n: LexicalNode | null = node;
    while (n) {
      const parent: LexicalNode | null = n.getParent();
      if (parent && $isRootOrShadowRoot(parent) && $isElementNode(n)) {
        blockKeys.add(n.getKey());
        break;
      }
      n = parent;
    }
  });
  const root = $getRoot();
  return root.getChildren().filter(
    (child): child is ElementNode => $isElementNode(child) && blockKeys.has(child.getKey()),
  );
}

/**
 * When selection is not collapsed, returns root-level ChecklistNodes that are the only blocks
 * in the selection (all selected root blocks are checklists). Returns null otherwise.
 */
export function getFullySelectedChecklistRoots(): ChecklistNode[] | null {
  const selection = $getSelection();
  if (!selection || !$isRangeSelection(selection) || selection.isCollapsed()) return null;
  const blocks = getSelectedRootBlocks();
  if (blocks.length === 0) return null;
  const checklists = blocks.filter((b): b is ChecklistNode => $isChecklistNode(b));
  if (checklists.length !== blocks.length) return null;
  return checklists;
}

/**
 * Replaces the given root-level checklists with a single empty paragraph and selects it.
 */
export function replaceSelectedChecklistsWithParagraph(checklists: ChecklistNode[]): void {
  if (checklists.length === 0) return;
  const paragraph = $createParagraphNode();
  checklists[0].replace(paragraph);
  checklists.slice(1).forEach((c) => c.remove());
  paragraph.selectStart();
}

/**
 * Converts multiple root-level blocks into a single checklist with one item per block.
 * Replaces the first block with the checklist and removes the rest.
 */
export function convertBlocksToChecklist(blocks: ElementNode[]): ChecklistItemNode | null {
  if (blocks.length === 0) return null;
  const listApiName = createChecklistApiName();
  const checklistRoot = $createChecklistNode({ listApiName });
  blocks.forEach((block) => {
    if ($isChecklistNode(block) || $isChecklistItemNode(block) || $isLexicalListNode(block)) return;
    const item = $createChecklistItemNode({
      listApiName,
      itemApiName: createChecklistSelectionApiName(),
    });
    const paragraph = $createParagraphNode();
    [...block.getChildren()].forEach((child) => paragraph.append(child));
    item.append(paragraph);
    checklistRoot.append(item);
  });
  if (checklistRoot.getChildrenSize() === 0) return null;
  const firstBlock = blocks[0];
  firstBlock.replace(checklistRoot);
  blocks.slice(1).forEach((block) => block.remove());
  const first = checklistRoot.getFirstChild();
  return first && $isChecklistItemNode(first) ? (first as ChecklistItemNode) : null;
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
  const paragraph = $createParagraphNode();
  block.getChildren().forEach((child) => paragraph.append(child));
  firstItem.append(paragraph);
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

/**
 * Converts a Lexical ListNode (bullet/number) into a ChecklistNode. Each ListItemNode becomes a ChecklistItemNode.
 */
export function convertListToChecklist(listNode: LexicalNode): ChecklistItemNode | null {
  if (!$isLexicalListNode(listNode)) return null;
  const list = listNode as import('@lexical/list').ListNode;
  const listType = list.getListType();
  if (listType === 'check') return null;
  const listApiName = createChecklistApiName();
  const checklistRoot = $createChecklistNode({ listApiName });
  const listItems = list.getChildren().filter((n): n is import('@lexical/list').ListItemNode => $isLexicalListItemNode(n));
  listItems.forEach((listItem) => {
    const checklistItem = $createChecklistItemNode({
      listApiName,
      itemApiName: createChecklistSelectionApiName(),
    });
    const paragraph = $createParagraphNode();
    const itemChildren = listItem.getChildren();
    itemChildren.forEach((child) => {
      if ($isParagraphNode(child)) {
        [...child.getChildren()].forEach((c) => paragraph.append(c));
      } else {
        paragraph.append(child);
      }
    });
    checklistItem.append(paragraph);
    checklistRoot.append(checklistItem);
  });
  list.replace(checklistRoot);
  const first = checklistRoot.getFirstChild();
  return first && $isChecklistItemNode(first) ? (first as ChecklistItemNode) : null;
}

/**
 * Converts a ChecklistNode into a Lexical ListNode (bullet or number). Each ChecklistItemNode becomes a ListItemNode.
 */
export function convertChecklistToList(checklistNode: LexicalNode, listType: 'number' | 'bullet'): import('@lexical/list').ListNode | null {
  if (!$isChecklistNode(checklistNode)) return null;
  const checklist = checklistNode as ChecklistNode;
  const lexicalList = $createLexicalListNode(listType);
  const items = checklist.getChildren().filter((n): n is ChecklistItemNode => $isChecklistItemNode(n));
  items.forEach((item) => {
    const listItem = $createLexicalListItemNode();
    [...item.getChildren()].forEach((child) => listItem.append(child));
    lexicalList.append(listItem);
  });
  checklist.replace(lexicalList);
  return lexicalList;
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

export function selectEndOfChecklistItem(item: ChecklistItemNode): void {
  ensureParagraphInChecklistItem(item);
  const textNode = item.getLastDescendant();
  if (textNode && $isTextNode(textNode)) {
    textNode.selectEnd();
    return;
  }
  const last = item.getLastChild();
  if (last && $isParagraphNode(last)) {
    last.selectEnd();
    return;
  }
  item.selectEnd();
}

export function getBackspaceOnEmptyChecklistPayload(): BackspaceOnEmptyChecklistPayload | null {
  const sel = $getSelection();
  if (!sel || !$isRangeSelection(sel) || !sel.isCollapsed()) return null;
  const item = getChecklistItemNodeFromSelection();
  if (!item || !isChecklistItemEmpty(item)) return null;
  const parent = item.getParent();
  return { itemKey: item.getKey(), parentKey: parent?.getKey() ?? null, prevItemKey: item.getPreviousSibling()?.getKey() ?? null };
}

export function isCursorAtStartOfChecklistItem(): string | null {
  const sel = $getSelection();
  if (!sel || !$isRangeSelection(sel) || !sel.isCollapsed()) return null;
  const { anchor } = sel;
  if (anchor.offset !== 0) return null;

  const item = getChecklistItemNodeFromSelection();
  if (!item || isChecklistItemEmpty(item)) return null;

  let node: LexicalNode | null = anchor.getNode();
  while (node && !node.is(item)) {
    if (node.getPreviousSibling()) return null;
    node = node.getParent();
  }
  return item.getKey();
}

/**
 * Splits the current checklist item at the selection: content to the right of the cursor
 * is moved into a new ChecklistItemNode inserted after the current item.
 */
export function applySplitChecklistEnter(): void {
  const selection = $getSelection();
  if (!selection || !$isRangeSelection(selection)) return;
  const newParagraph = selection.insertParagraph();
  if (!newParagraph || !$isParagraphNode(newParagraph)) return;
  const currentItem = newParagraph.getParent();
  if (!currentItem || !$isChecklistItemNode(currentItem)) return;
  const listApiName =
    currentItem.getParent() && $isChecklistNode(currentItem.getParent())
      ? (currentItem.getParent() as ChecklistNode).getListApiName()
      : currentItem.getListApiName();
  newParagraph.remove();
  const newItem = $createChecklistItemNode({
    listApiName,
    itemApiName: createChecklistSelectionApiName(),
  });
  newItem.append(newParagraph);
  currentItem.insertAfter(newItem);
  selectStartOfChecklistItem(newItem);
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

export function convertChecklistItemToParagraph(item: ChecklistItemNode): void {
  const parent = item.getParent();
  const paragraph = $createParagraphNode();
  item.getChildren().forEach((child) => {
    if ($isParagraphNode(child)) {
      child.getChildren().forEach((grandChild) => paragraph.append(grandChild));
    } else {
      paragraph.append(child);
    }
  });

  if (!parent || !$isChecklistNode(parent)) {
    item.replace(paragraph);
    paragraph.selectStart();
    return;
  }

  const siblings = parent.getChildren();
  const itemIndex = siblings.findIndex((s) => s.getKey() === item.getKey());
  const isOnly = siblings.length === 1;
  const isFirst = itemIndex === 0;
  const isLast = itemIndex === siblings.length - 1;

  if (isOnly) {
    parent.replace(paragraph);
  } else if (isFirst) {
    parent.insertBefore(paragraph);
    item.remove();
  } else if (isLast) {
    parent.insertAfter(paragraph);
    item.remove();
  } else {
    const afterItems = siblings.slice(itemIndex + 1);
    parent.insertAfter(paragraph);
    const newChecklist = $createChecklistNode({ listApiName: createChecklistApiName() });
    paragraph.insertAfter(newChecklist);
    afterItems.forEach((sibling) => {
      sibling.remove();
      newChecklist.append(sibling);
    });
    item.remove();
  }

  paragraph.selectStart();
}

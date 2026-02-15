/* eslint-disable class-methods-use-this */
/* eslint-disable no-underscore-dangle */
import {
  type DOMConversionMap,
  type DOMConversionOutput,
  type EditorConfig,
  type LexicalNode,
  type NodeKey,
  $applyNodeReplacement,
  ElementNode,
} from 'lexical';

import {
  CHECKLIST_ITEM_CLASS,
  CHECKBOX_CLASS,
} from './constants';
import type { SerializedChecklistItemNode, TChecklistItemNodePayload } from './types';

import styles from './ChecklistItemNode.css';

const CHECKLIST_LIST_ATTR = 'data-lexical-checklist-list';
const CHECKLIST_ITEM_ATTR = 'data-lexical-checklist-item';

export class ChecklistItemNode extends ElementNode {
  __listApiName: string;

  __itemApiName: string;

  static getType(): string {
    return 'checklist-item';
  }

  static clone(node: ChecklistItemNode): ChecklistItemNode {
    return new ChecklistItemNode(node.__listApiName, node.__itemApiName, node.getKey());
  }

  static importJSON(serialized: SerializedChecklistItemNode): ChecklistItemNode {
    return $createChecklistItemNode({
      listApiName: serialized.listApiName,
      itemApiName: serialized.itemApiName,
    });
  }

  constructor(listApiName: string, itemApiName: string, key?: NodeKey) {
    super(key);
    this.__listApiName = listApiName;
    this.__itemApiName = itemApiName;
  }

  getListApiName(): string {
    return this.__listApiName;
  }

  getItemApiName(): string {
    return this.__itemApiName;
  }

  createDOM(config: EditorConfig): HTMLElement {
    const li = document.createElement('li');
    li.className = `${styles['checklist-item']} ${CHECKLIST_ITEM_CLASS}`;
    li.setAttribute('data-lexical-checklist-list', this.__listApiName);
    li.setAttribute('data-lexical-checklist-item', this.__itemApiName);
    li.setAttribute('data-lexical-namespace', config.namespace);

    const checkbox = document.createElement('div');
    checkbox.className = `${CHECKBOX_CLASS} ${styles['checkbox']}`;
    checkbox.setAttribute('contenteditable', 'false');
    checkbox.setAttribute('tabindex', '-1');

    li.append(checkbox);
    return li;
  }

  exportDOM() {
    const li = document.createElement('li');
    li.className = CHECKLIST_ITEM_CLASS;
    li.setAttribute(CHECKLIST_LIST_ATTR, this.__listApiName);
    li.setAttribute(CHECKLIST_ITEM_ATTR, this.__itemApiName);
    return { element: li };
  }

  static importDOM(): DOMConversionMap<HTMLLIElement> | null {
    return {
      li: (domNode: HTMLLIElement) => {
        if (!domNode.hasAttribute(CHECKLIST_ITEM_ATTR)) return null;
        return {
          conversion: (element: HTMLLIElement): DOMConversionOutput => ({
            node: $createChecklistItemNode({
              listApiName: element.getAttribute(CHECKLIST_LIST_ATTR) ?? '',
              itemApiName: element.getAttribute(CHECKLIST_ITEM_ATTR) ?? '',
            }),
          }),
          priority: 1,
        };
      },
    };
  }

  updateDOM() {
    return false;
  }

  exportJSON(): SerializedChecklistItemNode {
    const json = super.exportJSON() as SerializedChecklistItemNode;
    return {
      ...json,
      type: 'checklist-item',
      version: 1,
      listApiName: this.__listApiName,
      itemApiName: this.__itemApiName,
    };
  }
}

export function $createChecklistItemNode(payload: TChecklistItemNodePayload): ChecklistItemNode {
  return $applyNodeReplacement(
    new ChecklistItemNode(payload.listApiName, payload.itemApiName),
  );
}

export function $isChecklistItemNode(
  node: LexicalNode | null | undefined,
): node is ChecklistItemNode {
  return node instanceof ChecklistItemNode;
}

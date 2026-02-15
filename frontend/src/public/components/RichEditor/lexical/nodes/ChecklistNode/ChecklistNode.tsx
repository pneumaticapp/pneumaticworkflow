/* eslint-disable no-underscore-dangle -- Lexical node internal field by convention */
import {
  type DOMConversionMap,
  type DOMConversionOutput,
  type EditorConfig,
  type LexicalNode,
  type NodeKey,
  type SerializedElementNode,
  ElementNode,
} from 'lexical';
import type { SerializedChecklistNode, TChecklistNodePayload } from './types';

const CHECKLIST_UL_CLASS = 'lexical-rich-editor-checklist-ul';
const CHECKLIST_LIST_ATTR = 'data-lexical-checklist-list';

export class ChecklistNode extends ElementNode {
  __listApiName: string;

  static getType(): string {
    return 'checklist';
  }

  static clone(node: ChecklistNode): ChecklistNode {
    return new ChecklistNode(node.__listApiName, node.getKey());
  }

  static importJSON(serialized: SerializedChecklistNode): ChecklistNode {
    const { format, direction, indent } = serialized as SerializedElementNode &
      SerializedChecklistNode;
    const node = new ChecklistNode(serialized.listApiName);
    node.setFormat(format);
    node.setDirection(direction);
    node.setIndent(indent);
    return node;
  }

  constructor(listApiName: string, key?: NodeKey) {
    super(key);
    this.__listApiName = listApiName;
  }

  getListApiName(): string {
    return this.__listApiName;
  }

  setListApiName(listApiName: string): this {
    const self = this.getWritable();
    self.__listApiName = listApiName;
    return self;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- Lexical createDOM(config) signature
  createDOM(_config: EditorConfig): HTMLElement {
    const ul = document.createElement('ul');
    ul.className = CHECKLIST_UL_CLASS;
    ul.setAttribute('data-lexical-checklist-list', this.__listApiName);
    return ul;
  }

  // eslint-disable-next-line class-methods-use-this -- Lexical ElementNode.updateDOM() override
  updateDOM(): boolean {
    return false;
  }

  exportDOM(): { element: HTMLUListElement } {
    const ul = document.createElement('ul');
    ul.className = CHECKLIST_UL_CLASS;
    ul.setAttribute(CHECKLIST_LIST_ATTR, this.__listApiName);
    return { element: ul };
  }

  static importDOM(): DOMConversionMap<HTMLUListElement> | null {
    return {
      ul: (domNode: HTMLUListElement) => {
        const isChecklist =
          domNode.hasAttribute(CHECKLIST_LIST_ATTR) ||
          domNode.classList.contains(CHECKLIST_UL_CLASS);
        if (!isChecklist) return null;
        return {
          conversion: (element: HTMLUListElement): DOMConversionOutput => ({
            node: $createChecklistNode({
              listApiName: element.getAttribute(CHECKLIST_LIST_ATTR) ?? '',
            }),
          }),
          priority: 1,
        };
      },
    };
  }

  exportJSON(): SerializedChecklistNode {
    const json = super.exportJSON() as SerializedChecklistNode;
    return {
      ...json,
      type: 'checklist',
      version: 1,
      listApiName: this.__listApiName,
    };
  }

  // eslint-disable-next-line class-methods-use-this -- Lexical ElementNode.isInline() override
  isInline(): boolean {
    return false;
  }
}

export function $createChecklistNode(payload: TChecklistNodePayload): ChecklistNode {
  return new ChecklistNode(payload.listApiName);
}

export function $isChecklistNode(
  node: LexicalNode | null | undefined,
): node is ChecklistNode {
  return node instanceof ChecklistNode;
}

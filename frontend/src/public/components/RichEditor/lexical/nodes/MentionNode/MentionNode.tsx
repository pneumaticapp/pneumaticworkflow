import React from 'react';
import {
  type LexicalNode,
  type NodeKey,
  type SerializedLexicalNode,
  type DOMConversionMap,
  type DOMConversionOutput,
  type DOMExportOutput,
  DecoratorNode,
  $applyNodeReplacement,
} from 'lexical';

export type SerializedMentionNode = SerializedLexicalNode & {
  type: 'mention';
  version: 1;
  id: number;
  name: string;
  link?: string;
};

export type TMentionNodePayload = {
  id: number;
  name: string;
  link?: string;
};

function MentionComponent({ name }: { name: string }): React.ReactElement {
  return <span className="lexical-rich-editor-mention">@{name}</span>;
}

export interface IMentionNode {
  getType(): string;
  getId(): number;
  getName(): string;
  getLink(): string | undefined;
  exportJSON(): SerializedMentionNode;
}

export class MentionNode extends DecoratorNode<React.ReactElement> {
  private readonly mentionId: number;

  private readonly mentionName: string;

  private readonly mentionLink?: string;

  static getType(): string {
    return 'mention';
  }

  static clone(node: MentionNode): MentionNode {
    return new MentionNode(
      node.mentionId,
      node.mentionName,
      node.mentionLink,
      node.getKey(),
    );
  }

  static importJSON(serialized: SerializedMentionNode): MentionNode {
    return $createMentionNode({
      id: serialized.id,
      name: serialized.name,
      link: serialized.link,
    });
  }

  constructor(id: number, name: string, link?: string, key?: NodeKey) {
    super(key);
    this.mentionId = id;
    this.mentionName = name;
    this.mentionLink = link;
  }

  getId(): number {
    return this.mentionId;
  }

  getName(): string {
    return this.mentionName;
  }

  getLink(): string | undefined {
    return this.mentionLink;
  }

  // eslint-disable-next-line class-methods-use-this -- Lexical DecoratorNode override
  isInline(): boolean {
    return true;
  }

  // eslint-disable-next-line class-methods-use-this -- Lexical DecoratorNode override
  isIsolated(): boolean {
    return true;
  }

  getTextContent(): string {
    return `@${this.mentionName}`;
  }

  static importDOM(): DOMConversionMap<HTMLSpanElement> | null {
    return {
      span: (domNode: HTMLSpanElement) => {
        if (!domNode.hasAttribute('data-lexical-mention')) return null;
        return {
          conversion: (element: HTMLSpanElement): DOMConversionOutput => {
            const id = parseInt(element.getAttribute('data-lexical-mention-id') ?? '0', 10);
            const name = element.getAttribute('data-lexical-mention-name') ?? '';
            const link = element.getAttribute('data-lexical-mention-link');
            return {
              node: $createMentionNode({ id, name, link: link ?? undefined }),
            };
          },
          priority: 2,
        };
      },
    };
  }

  exportDOM(): DOMExportOutput {
    const span = document.createElement('span');
    span.setAttribute('data-lexical-decorator', this.getType());
    span.setAttribute('data-lexical-mention', 'true');
    span.setAttribute('data-lexical-mention-id', String(this.mentionId));
    span.setAttribute('data-lexical-mention-name', this.mentionName);
    if (this.mentionLink != null) {
      span.setAttribute('data-lexical-mention-link', this.mentionLink);
    }
    span.setAttribute('contenteditable', 'false');
    span.textContent = `@${this.mentionName}`;
    return { element: span };
  }

  exportJSON(): SerializedMentionNode {
    return {
      type: 'mention',
      version: 1,
      id: this.mentionId,
      name: this.mentionName,
      link: this.mentionLink,
    };
  }

  createDOM(): HTMLElement {
    const span = document.createElement('span');
    span.setAttribute('data-lexical-decorator', this.getType());
    span.setAttribute('contenteditable', 'false');
    return span;
  }

  updateDOM(): false {
    this.getType();
    return false;
  }

  decorate(): React.ReactElement {
    return <MentionComponent name={this.mentionName} />;
  }
}

export function $createMentionNode(payload: TMentionNodePayload): MentionNode {
  return $applyNodeReplacement(
    new MentionNode(payload.id, payload.name, payload.link),
  );
}

export function $isMentionNode(
  node: LexicalNode | null | undefined,
): node is MentionNode {
  return node instanceof MentionNode;
}

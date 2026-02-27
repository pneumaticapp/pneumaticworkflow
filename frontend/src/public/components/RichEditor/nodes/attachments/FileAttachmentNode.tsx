import React, { useCallback } from 'react';
import {
  DecoratorNode,
  type LexicalNode,
  type NodeKey,
  type SerializedLexicalNode,
  type DOMConversionMap,
  type DOMConversionOutput,
  type DOMExportOutput,
  $applyNodeReplacement,
  $getNodeByKey,
} from 'lexical';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { DocumentAttachment } from '../../../Attachments/DocumentAttachment';
import type { TAttachmentPayload } from './types';

export type SerializedFileAttachmentNode = TAttachmentPayload & SerializedLexicalNode;

function FileAttachmentComponent({
  nodeKey,
  url,
  name,
}: {
  nodeKey: NodeKey;
  url: string;
  name?: string;
}): React.ReactElement {
  const [editor] = useLexicalComposerContext();
  const deleteFile = useCallback(() => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if (node) {
        node.remove();
      }
    });
  }, [editor, nodeKey]);

  return (
    <DocumentAttachment
      url={url}
      name={name ?? url}
      isEdit
      isClickable={false}
      deleteFile={deleteFile}
    />
  );
}

export class FileAttachmentNode extends DecoratorNode<React.ReactElement> {
  attachmentUrl: string;

  attachmentId?: number;

  attachmentName?: string;

  static getType(): string {
    return 'file-attachment';
  }

  static clone(node: FileAttachmentNode): FileAttachmentNode {
    return new FileAttachmentNode(
      node.attachmentUrl,
      node.attachmentId,
      node.attachmentName,
      node.getKey(),
    );
  }

  static importJSON(serialized: SerializedFileAttachmentNode): FileAttachmentNode {
    return $createFileAttachmentNode(serialized);
  }

  static importDOM(): DOMConversionMap<HTMLDivElement> | null {
    return {
      div: (domNode: HTMLDivElement) => {
        if (domNode.getAttribute('data-lexical-file-attachment') == null) return null;
        return {
          conversion: (element: HTMLDivElement): DOMConversionOutput => {
            const url = element.getAttribute('data-lexical-attachment-url') ?? '';
            const rawId = element.getAttribute('data-lexical-attachment-id');
            const id = rawId != null ? parseInt(rawId, 10) : undefined;
            const name = element.getAttribute('data-lexical-attachment-name') ?? undefined;
            return { node: $createFileAttachmentNode({ url, id, name }) };
          },
          priority: 2,
        };
      },
    };
  }

  constructor(url: string, id?: number, name?: string, key?: NodeKey) {
    super(key);
    this.attachmentUrl = url;
    this.attachmentId = id;
    this.attachmentName = name;
  }

  exportJSON(): SerializedFileAttachmentNode {
    return {
      ...super.exportJSON(),
      type: 'file-attachment',
      version: 1,
      url: this.attachmentUrl,
      id: this.attachmentId,
      name: this.attachmentName,
    };
  }

  exportDOM(): DOMExportOutput {
    const div = document.createElement('div');
    div.setAttribute('data-lexical-decorator', this.getType());
    div.setAttribute('data-lexical-file-attachment', 'true');
    div.setAttribute('data-lexical-attachment-url', this.attachmentUrl);
    if (this.attachmentId != null) {
      div.setAttribute('data-lexical-attachment-id', String(this.attachmentId));
    }
    if (this.attachmentName != null) {
      div.setAttribute('data-lexical-attachment-name', this.attachmentName);
    }
    const anchor = document.createElement('a');
    anchor.href = this.attachmentUrl;
    anchor.textContent = this.attachmentName ?? this.attachmentUrl;
    div.appendChild(anchor);
    return { element: div };
  }

  createDOM(): HTMLElement {
    const div = document.createElement('div');
    div.setAttribute('data-lexical-decorator', this.getType());
    return div;
  }

  updateDOM(): false {
    return (this.getType(), false);
  }

  decorate(): React.ReactElement {
    return (
      <FileAttachmentComponent
        nodeKey={this.getKey()}
        url={this.attachmentUrl}
        name={this.attachmentName}
      />
    );
  }
}

export function $createFileAttachmentNode(
  payload: TAttachmentPayload,
): FileAttachmentNode {
  return $applyNodeReplacement(
    new FileAttachmentNode(payload.url, payload.id, payload.name),
  );
}

export function $isFileAttachmentNode(
  node: LexicalNode | null | undefined,
): node is FileAttachmentNode {
  return node instanceof FileAttachmentNode;
}

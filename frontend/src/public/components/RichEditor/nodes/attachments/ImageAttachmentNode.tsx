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
import { ImageAttachment } from '../../../Attachments/ImageAttachment';
import type { TAttachmentPayload } from './types';

export type SerializedImageAttachmentNode = TAttachmentPayload & SerializedLexicalNode;

function ImageAttachmentComponent({
  nodeKey,
  url,
}: {
  nodeKey: NodeKey;
  url: string;
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
    <ImageAttachment
      thumbnailUrl={url}
      url={url}
      isEdit
      deleteFile={deleteFile}
    />
  );
}

export class ImageAttachmentNode extends DecoratorNode<React.ReactElement> {
  attachmentUrl: string;

  attachmentId?: number;

  attachmentName?: string;

  static getType(): string {
    return 'image-attachment';
  }

  static clone(node: ImageAttachmentNode): ImageAttachmentNode {
    return new ImageAttachmentNode(
      node.attachmentUrl,
      node.attachmentId,
      node.attachmentName,
      node.getKey(),
    );
  }

  static importJSON(serialized: SerializedImageAttachmentNode): ImageAttachmentNode {
    return $createImageAttachmentNode(serialized);
  }

  static importDOM(): DOMConversionMap<HTMLDivElement> | null {
    return {
      div: (domNode: HTMLDivElement) => {
        if (domNode.getAttribute('data-lexical-image-attachment') == null) return null;
        return {
          conversion: (element: HTMLDivElement): DOMConversionOutput => {
            const url = element.getAttribute('data-lexical-attachment-url') ?? '';
            const rawId = element.getAttribute('data-lexical-attachment-id');
            const id = rawId != null ? parseInt(rawId, 10) : undefined;
            const name = element.getAttribute('data-lexical-attachment-name') ?? undefined;
            return { node: $createImageAttachmentNode({ url, id, name }) };
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

  exportJSON(): SerializedImageAttachmentNode {
    return {
      ...super.exportJSON(),
      type: 'image-attachment',
      version: 1,
      url: this.attachmentUrl,
      id: this.attachmentId,
      name: this.attachmentName,
    };
  }

  exportDOM(): DOMExportOutput {
    const div = document.createElement('div');
    div.setAttribute('data-lexical-decorator', this.getType());
    div.setAttribute('data-lexical-image-attachment', 'true');
    div.setAttribute('data-lexical-attachment-url', this.attachmentUrl);
    if (this.attachmentId != null) {
      div.setAttribute('data-lexical-attachment-id', String(this.attachmentId));
    }
    if (this.attachmentName != null) {
      div.setAttribute('data-lexical-attachment-name', this.attachmentName);
    }
    const img = document.createElement('img');
    img.src = this.attachmentUrl;
    img.alt = this.attachmentName ?? '';
    div.appendChild(img);
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
      <ImageAttachmentComponent nodeKey={this.getKey()} url={this.attachmentUrl} />
    );
  }
}

export function $createImageAttachmentNode(
  payload: TAttachmentPayload,
): ImageAttachmentNode {
  return $applyNodeReplacement(
    new ImageAttachmentNode(payload.url, payload.id, payload.name),
  );
}

export function $isImageAttachmentNode(
  node: LexicalNode | null | undefined,
): node is ImageAttachmentNode {
  return node instanceof ImageAttachmentNode;
}

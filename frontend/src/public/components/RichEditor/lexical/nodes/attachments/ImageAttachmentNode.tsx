import React, { useCallback } from 'react';
import {
  DecoratorNode,
  type LexicalNode,
  type NodeKey,
  type SerializedLexicalNode,
  $applyNodeReplacement,
  $getNodeByKey,
} from 'lexical';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { ImageAttachment } from '../../../../Attachments/ImageAttachment';
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

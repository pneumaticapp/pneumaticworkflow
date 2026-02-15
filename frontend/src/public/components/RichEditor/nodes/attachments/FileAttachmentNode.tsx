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

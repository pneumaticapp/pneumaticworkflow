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
import { DeleteBoldIcon } from '../../../../icons';
import type { TAttachmentPayload } from './types';
import styles from './VideoAttachmentNode.css';

export type SerializedVideoAttachmentNode = TAttachmentPayload & SerializedLexicalNode;

function VideoAttachmentComponent({
  nodeKey,
  url,
}: {
  nodeKey: NodeKey;
  url: string;
}): React.ReactElement {
  const [editor] = useLexicalComposerContext();
  const onDelete = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation();
      e.preventDefault();
      editor.update(() => {
        const node = $getNodeByKey(nodeKey);
        if (node) {
          node.remove();
        }
      });
    },
    [editor, nodeKey],
  );

  return (
    <div className={styles.container} role="group">
      <video
        src={url}
        preload="auto"
        className={styles.video}
        controls
        onClick={(e) => e.stopPropagation()}
      >
        <track kind="captions" />
      </video>
      <button
        type="button"
        aria-label="Delete video"
        className={styles.delete}
        onClick={onDelete}
      >
        <DeleteBoldIcon />
      </button>
    </div>
  );
}

export class VideoAttachmentNode extends DecoratorNode<React.ReactElement> {
  attachmentUrl: string;

  attachmentId?: number;

  attachmentName?: string;

  static getType(): string {
    return 'video-attachment';
  }

  static clone(node: VideoAttachmentNode): VideoAttachmentNode {
    return new VideoAttachmentNode(
      node.attachmentUrl,
      node.attachmentId,
      node.attachmentName,
      node.getKey(),
    );
  }

  static importJSON(
    serialized: SerializedVideoAttachmentNode,
  ): VideoAttachmentNode {
    return $createVideoAttachmentNode(serialized);
  }

  constructor(url: string, id?: number, name?: string, key?: NodeKey) {
    super(key);
    this.attachmentUrl = url;
    this.attachmentId = id;
    this.attachmentName = name;
  }

  exportJSON(): SerializedVideoAttachmentNode {
    return {
      ...super.exportJSON(),
      type: 'video-attachment',
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
      <VideoAttachmentComponent nodeKey={this.getKey()} url={this.attachmentUrl} />
    );
  }
}

export function $createVideoAttachmentNode(
  payload: TAttachmentPayload,
): VideoAttachmentNode {
  return $applyNodeReplacement(
    new VideoAttachmentNode(payload.url, payload.id, payload.name),
  );
}

export function $isVideoAttachmentNode(
  node: LexicalNode | null | undefined,
): node is VideoAttachmentNode {
  return node instanceof VideoAttachmentNode;
}

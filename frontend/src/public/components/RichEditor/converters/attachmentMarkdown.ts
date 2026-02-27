import type { ElementTransformer } from '@lexical/markdown';
import {
  ImageAttachmentNode,
  VideoAttachmentNode,
  FileAttachmentNode,
  $createImageAttachmentNode,
  $isImageAttachmentNode,
  $createVideoAttachmentNode,
  $isVideoAttachmentNode,
  $createFileAttachmentNode,
  $isFileAttachmentNode,
} from '../nodes/attachments';
import { ECustomEditorEntities } from '../utils/types';

type TAttachmentEntityType = ECustomEditorEntities.Image | ECustomEditorEntities.Video | ECustomEditorEntities.File;

function buildAttachmentMarkdown(
  name: string,
  url: string,
  id: number | undefined,
  entityType: TAttachmentEntityType,
): string {
  const idPart = id != null ? `attachment_id:${id} ` : '';
  return `![${name}](${url} "${idPart}entityType:${entityType}")`;
}

const ATTACHMENT_RE =
  /^!?\[([^\]]*)\]\((.*?)\s*"(?:attachment_id:(\d*)\s*)?entityType:(image|video|file)[^"]*"\s*\)$/;

const nodeCreators = {
  [ECustomEditorEntities.Image]: $createImageAttachmentNode,
  [ECustomEditorEntities.Video]: $createVideoAttachmentNode,
  [ECustomEditorEntities.File]: $createFileAttachmentNode,
} as const;

export const ATTACHMENT: ElementTransformer = {
  dependencies: [ImageAttachmentNode, VideoAttachmentNode, FileAttachmentNode],
  export: (node) => {
    if ($isImageAttachmentNode(node)) {
      return buildAttachmentMarkdown(
        node.attachmentName ?? '',
        node.attachmentUrl,
        node.attachmentId,
        ECustomEditorEntities.Image,
      );
    }
    if ($isVideoAttachmentNode(node)) {
      return buildAttachmentMarkdown(
        node.attachmentName ?? '',
        node.attachmentUrl,
        node.attachmentId,
        ECustomEditorEntities.Video,
      );
    }
    if ($isFileAttachmentNode(node)) {
      return buildAttachmentMarkdown(
        node.attachmentName ?? '',
        node.attachmentUrl,
        node.attachmentId,
        ECustomEditorEntities.File,
      );
    }
    return null;
  },
  regExp: ATTACHMENT_RE,
  replace: (parentNode, _children, match) => {
    const name = match[1] ?? '';
    const url = (match[2] ?? '').trim();
    const id = match[3] ? parseInt(match[3], 10) : undefined;
    const entityType = match[4] as TAttachmentEntityType;

    const create = nodeCreators[entityType];
    const node = create({ url, id, name });
    parentNode.replace(node);
  },
  type: 'element',
};

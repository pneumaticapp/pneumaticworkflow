import type { ElementTransformer, TextMatchTransformer } from '@lexical/markdown';
import { $createParagraphNode, $isTextNode } from 'lexical';
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
import { buildAttachmentMarkdownString } from '../nodes/attachments/attachmentMarkdownFormat';
import { ECustomEditorEntities } from '../utils/types';

type TAttachmentEntityType = ECustomEditorEntities.Image | ECustomEditorEntities.Video | ECustomEditorEntities.File;

/** Full-line match for block-level import (line is only the image). */
const ATTACHMENT_RE =
  /^!?\[([^\]]*)\]\((.*?)\s*"(?:attachment_id:(\d*)\s*)?entityType:(image|video|file)[^"]*"\)?$/;

/** Inline match when line was merged by normalizeMarkdown (image inside a line). */
export const ATTACHMENT_IMPORT_RE =
  /!?\[([^\]]*)\]\((.*?)\s*"(?:attachment_id:(\d*)\s*)?entityType:(image|video|file)[^"]*"\)?/;

const nodeCreators = {
  [ECustomEditorEntities.Image]: $createImageAttachmentNode,
  [ECustomEditorEntities.Video]: $createVideoAttachmentNode,
  [ECustomEditorEntities.File]: $createFileAttachmentNode,
} as const;

function createAttachmentNodeFromMatch(
  match: RegExpMatchArray | string[],
): ReturnType<typeof $createImageAttachmentNode> {
  const name = match[1] ?? '';
  const url = (match[2] ?? '').trim();
  const id = match[3] ? parseInt(String(match[3]), 10) : undefined;
  const entityType = (match[4] ?? '') as TAttachmentEntityType;
  const create = nodeCreators[entityType];
  return create({ url, id, name });
}

export const ATTACHMENT: ElementTransformer = {
  dependencies: [ImageAttachmentNode, VideoAttachmentNode, FileAttachmentNode],
  export: (node) => {
    if ($isImageAttachmentNode(node)) {
      return buildAttachmentMarkdownString(
        node.attachmentName ?? '',
        node.attachmentUrl,
        node.attachmentId,
        ECustomEditorEntities.Image,
      );
    }
    if ($isVideoAttachmentNode(node)) {
      return buildAttachmentMarkdownString(
        node.attachmentName ?? '',
        node.attachmentUrl,
        node.attachmentId,
        ECustomEditorEntities.Video,
      );
    }
    if ($isFileAttachmentNode(node)) {
      return buildAttachmentMarkdownString(
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
    const node = createAttachmentNodeFromMatch(match);
    const paragraph = $createParagraphNode();
    paragraph.append(node);
    parentNode.replace(paragraph);
  },
  type: 'element',
};

/**
 * Inline (text-match) transformer so attachments are recognized when the line
 * was merged with others by normalizeMarkdown, e.g. "text ![img](url \"entityType:image\") more".
 * Ensures image previews render after reload.
 */
export const ATTACHMENT_INLINE: TextMatchTransformer = {
  dependencies: [ImageAttachmentNode, VideoAttachmentNode, FileAttachmentNode],
  importRegExp: ATTACHMENT_IMPORT_RE,
  regExp: ATTACHMENT_IMPORT_RE,
  replace: (replaceNode, match) => {
    const node = createAttachmentNodeFromMatch(match);
    replaceNode.replace(node);
    const next = node.getNextSibling();
    if (next && $isTextNode(next)) {
      const text = next.getTextContent();
      const trimmed = text.replace(/^[\n\r]+/, '');
      if (trimmed !== text) {
        next.setTextContent(trimmed);
      }
    }
  },
  trigger: '"',
  type: 'text-match',
};

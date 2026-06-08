import type { TextMatchTransformer } from '@lexical/markdown';
import { $createLinkNode, LinkNode, $isLinkNode } from '@lexical/link';
import { $createTextNode, $isTextNode } from 'lexical';
import {
  escapeMarkdownLinkText,
  GENERAL_MARKDOWN_LINK_IMPORT_RE,
  unescapeMarkdownLinkText,
} from '../utils/converters/markdownLinkText';

const LINK_LINE_RE = new RegExp(`^${GENERAL_MARKDOWN_LINK_IMPORT_RE.source}$`);

const ATTACHMENT_ENTITY_TYPES = new Set(['image', 'video', 'file']);

export const MARKDOWN_LINK: TextMatchTransformer = {
  dependencies: [LinkNode],
  export: (node, _exportChildren, exportFormat) => {
    if (!$isLinkNode(node)) {
      return null;
    }

    const title = node.getTitle();
    const escapedText = escapeMarkdownLinkText(node.getTextContent());
    const linkContent = title
      ? `[${escapedText}](${node.getURL()} "${title}")`
      : `[${escapedText}](${node.getURL()})`;
    const firstChild = node.getFirstChild();

    if (node.getChildrenSize() === 1 && $isTextNode(firstChild)) {
      return exportFormat(firstChild, linkContent);
    }

    return linkContent;
  },
  importRegExp: GENERAL_MARKDOWN_LINK_IMPORT_RE,
  regExp: LINK_LINE_RE,
  replace: (textNode, match) => {
    const attachmentEntityType = match[4];
    if (attachmentEntityType != null && ATTACHMENT_ENTITY_TYPES.has(attachmentEntityType)) {
      return;
    }

    const linkText = unescapeMarkdownLinkText(match[1] ?? '');
    const linkUrl = (match[2] ?? '').trim();
    const linkNode = $createLinkNode(linkUrl);
    const linkTextNode = $createTextNode(linkText);
    linkTextNode.setFormat(textNode.getFormat());
    linkNode.append(linkTextNode);
    textNode.replace(linkNode);
  },
  trigger: ')',
  type: 'text-match',
};

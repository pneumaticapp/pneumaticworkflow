import type { TextMatchTransformer } from '@lexical/markdown';
import { mentionsRegex } from '../../../constants/defaultValues';
import { escapeMarkdownLinkText, unescapeMarkdownLinkText } from '../utils/converters/markdownLinkText';
import { MentionNode, $createMentionNode, $isMentionNode } from '../nodes/MentionNode';

export const MENTION: TextMatchTransformer = {
  dependencies: [MentionNode],
  export: (node) =>
    $isMentionNode(node)
      ? `[${escapeMarkdownLinkText(node.getName())}|${node.getId()}]`
      : null,
  importRegExp: new RegExp(mentionsRegex.source, mentionsRegex.flags),
  regExp: new RegExp(mentionsRegex.source, mentionsRegex.flags),
  replace: (textNode, match) => {
    const name = unescapeMarkdownLinkText(match[1] ?? '');
    const idStr = match[2] ?? '0';
    const id = parseInt(idStr, 10);
    if (Number.isNaN(id)) {
      return;
    }
    const mentionNode = $createMentionNode({ id, name });
    textNode.replace(mentionNode);
  },
  type: 'text-match',
};

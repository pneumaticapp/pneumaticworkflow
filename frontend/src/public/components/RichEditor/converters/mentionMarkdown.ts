import type { TextMatchTransformer } from '@lexical/markdown';
import { $createTextNode, $isTextNode } from 'lexical';
import { mentionsRegex } from '../../../constants/defaultValues';
import { MentionNode, $createMentionNode, $isMentionNode } from '../nodes/MentionNode';

export const MENTION: TextMatchTransformer = {
  dependencies: [MentionNode],
  export: (node) =>
    $isMentionNode(node)
      ? `[${node.getName()}|${node.getId()}]`
      : null,
  importRegExp: new RegExp(mentionsRegex.source, mentionsRegex.flags),
  regExp: new RegExp(mentionsRegex.source, mentionsRegex.flags),
  replace: (textNode, match) => {
    const name = match[1] ?? '';
    const idStr = match[2] ?? '0';
    const id = parseInt(idStr, 10);
    if (Number.isNaN(id)) {
      return;
    }
    const mentionNode = $createMentionNode({ id, name });
    textNode.replace(mentionNode);
    const next = mentionNode.getNextSibling();
    const hasSpaceAfter =
      next && $isTextNode(next) && next.getTextContent().startsWith(' ');
    if (!hasSpaceAfter) {
      mentionNode.insertAfter($createTextNode(' '));
    }
  },
  type: 'text-match',
};

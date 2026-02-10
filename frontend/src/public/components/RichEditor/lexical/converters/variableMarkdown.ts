import type { TextMatchTransformer } from '@lexical/markdown';
import type { LexicalNode } from 'lexical';
import { $createTextNode } from 'lexical';

import { mentionsRegex, variableRegex } from '../../../../constants/defaultValues';
import { $createMentionNode } from '../nodes/MentionNode';
import { VariableNode, $createVariableNode, $isVariableNode } from '../nodes/VariableNode';
import type { TTaskVariable } from '../../../TemplateEdit/types';

type InlineMatch =
  | { type: 'variable'; index: number; end: number; match: RegExpMatchArray }
  | { type: 'mention'; index: number; end: number; match: RegExpMatchArray };

function createVariableNodeFromApiName(
  apiName: string,
  templateVariables?: TTaskVariable[],
): ReturnType<typeof $createVariableNode> {
  const variable = templateVariables?.find((v) => v.apiName === apiName);
  return $createVariableNode({
    apiName: variable?.apiName ?? apiName,
    title: variable?.title ?? apiName,
    subtitle: variable?.subtitle,
  });
}

function findAllInlineMatches(text: string): InlineMatch[] {
  const reVar = new RegExp(variableRegex.source, `${variableRegex.flags}g`);
  const reMention = new RegExp(mentionsRegex.source, `${mentionsRegex.flags}g`);
  const list: InlineMatch[] = [
    ...[...text.matchAll(reVar)].map((match) => ({
      type: 'variable' as const,
      index: match.index!,
      end: match.index! + match[0].length,
      match,
    })),
    ...[...text.matchAll(reMention)].map((match) => ({
      type: 'mention' as const,
      index: match.index!,
      end: match.index! + match[0].length,
      match,
    })),
  ].sort((a, b) => a.index - b.index);
  const { filtered } = list.reduce<{ filtered: InlineMatch[]; lastEnd: number }>(
    (acc, item) => {
      if (item.index >= acc.lastEnd) {
        acc.filtered.push(item);
        acc.lastEnd = item.end;
      }
      return acc;
    },
    { filtered: [], lastEnd: 0 },
  );
  return filtered;
}

function matchToNode(item: InlineMatch, templateVariables?: TTaskVariable[]): LexicalNode {
  if (item.type === 'variable') {
    return createVariableNodeFromApiName(item.match[1] ?? '', templateVariables);
  }
  const name = item.match[1] ?? '';
  const id = parseInt(item.match[2] ?? '0', 10);
  if (!Number.isNaN(id)) return $createMentionNode({ id, name });
  return $createTextNode(item.match[0]);
}

export function parseTextWithVariables(
  text: string,
  templateVariables?: TTaskVariable[],
): LexicalNode[] {
  const matches = findAllInlineMatches(text);
  if (matches.length === 0) {
    return [$createTextNode(text)];
  }
  const { nodes, lastIndex } = matches.reduce<{
    nodes: LexicalNode[];
    lastIndex: number;
  }>(
    (acc, item) => {
      if (item.index > acc.lastIndex) {
        acc.nodes.push($createTextNode(text.slice(acc.lastIndex, item.index)));
      }
      acc.nodes.push(matchToNode(item, templateVariables));
      acc.lastIndex = item.end;
      return acc;
    },
    { nodes: [], lastIndex: 0 },
  );
  if (lastIndex < text.length) {
    nodes.push($createTextNode(text.slice(lastIndex)));
  }
  return nodes;
}

export function createVariableTransformer(
  templateVariables?: TTaskVariable[],
): TextMatchTransformer {
  return {
    dependencies: [VariableNode],
    export: (node) =>
      $isVariableNode(node) ? `{{${node.getApiName()}}}` : null,
    importRegExp: variableRegex,
    regExp: variableRegex,
    replace: (textNode, match) => {
      const node = createVariableNodeFromApiName(match[1] ?? '', templateVariables);
      textNode.replace(node);
      node.insertAfter($createTextNode(' '));
    },
    type: 'text-match',
  };
}

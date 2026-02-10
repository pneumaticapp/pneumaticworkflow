import type { MultilineElementTransformer } from '@lexical/markdown';
import type { ElementNode } from 'lexical';
import { $createParagraphNode } from 'lexical';
import {
  ChecklistNode,
  ChecklistItemNode,
  $createChecklistNode,
  $createChecklistItemNode,
  $isChecklistNode,
  $isChecklistItemNode,
} from '../nodes';
import { parseTextWithVariables } from './variableMarkdown';
import type { TTaskVariable } from '../../../TemplateEdit/types';

const CLIST_START_REGEX = /\[clist:([\w-]+)\|([\w-]+)\]/;
const CLIST_END_REGEX = /\[\/clist\]/;

export function createChecklistTransformer(
  templateVariables?: TTaskVariable[],
): MultilineElementTransformer {
  return {
    dependencies: [ChecklistNode, ChecklistItemNode],
    regExpStart: CLIST_START_REGEX,
    regExpEnd: CLIST_END_REGEX,
    export: (node, traverseChildren) => {
      if ($isChecklistNode(node)) {
        const parts = node.getChildren().map((child) => {
          if ($isChecklistItemNode(child)) {
            const content = traverseChildren(child as ElementNode);
            return `[clist:${child.getListApiName()}|${child.getItemApiName()}]${content}[/clist]`;
          }
          return traverseChildren(child as ElementNode);
        });
        return parts.join('\n');
      }
      if ($isChecklistItemNode(node)) {
        const content = traverseChildren(node as ElementNode);
        return `[clist:${node.getListApiName()}|${node.getItemApiName()}]${content}[/clist]`;
      }
      return null;
    },
    replace: (rootNode, _children, startMatch, _endMatch, linesInBetween, isImport) => {
      if (!isImport || !linesInBetween) return false;
      const listApiName = startMatch[1] ?? '';
      const itemApiName = startMatch[2] ?? '';
      const value = linesInBetween.join('\n').trim();
      const itemNode = $createChecklistItemNode({
        listApiName,
        itemApiName,
      });
      const paragraph = $createParagraphNode();
      const contentNodes = parseTextWithVariables(value, templateVariables);
      contentNodes.forEach((n) => paragraph.append(n));
      itemNode.clear();
      itemNode.append(paragraph);

      const lastChild = rootNode.getLastChild();
      if (lastChild != null && $isChecklistNode(lastChild) && lastChild.getListApiName() === listApiName) {
        lastChild.getWritable().append(itemNode);
      } else if (
        lastChild != null &&
        $isChecklistItemNode(lastChild) &&
        lastChild.getListApiName() === listApiName
      ) {
        const parent = lastChild.getParent();
        if (parent != null && $isChecklistNode(parent)) {
          parent.getWritable().append(itemNode);
        } else {
          const newRoot = $createChecklistNode({ listApiName });
          newRoot.append(itemNode);
          rootNode.append(newRoot);
        }
      } else {
        const newRoot = $createChecklistNode({ listApiName });
        newRoot.append(itemNode);
        rootNode.append(newRoot);
      }
      return true;
    },
    type: 'multiline-element',
  };
}

import type { EditorState, LexicalNode } from 'lexical';
import { $getRoot, $isElementNode, $isTextNode } from 'lexical';

import { $isVariableNode } from '../nodes/VariableNode';



function serializeNodeToPlainText(node: LexicalNode): string {
  if ($isVariableNode(node)) {
    return `{{${node.getApiName()}}}`;
  }

  if ($isTextNode(node)) {
    return node.getTextContent();
  }

  if ($isElementNode(node)) {
    return node.getChildren().map(serializeNodeToPlainText).join('');
  }

  return '';
}

export function serializeEditorToPlainTextWithVariables(editorState: EditorState): string {
  let result = '';

  editorState.read(() => {
    const root = $getRoot();
    result = root.getChildren().map(serializeNodeToPlainText).join('');
  });

  return result;
}

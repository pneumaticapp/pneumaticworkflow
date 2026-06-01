import type { EditorState } from 'lexical';

import { serializeEditorToPlainTextWithVariables } from './serializePlainTextWithVariables';



export function convertLexicalToPlainText(editorState: EditorState): string {
  try {
    return serializeEditorToPlainTextWithVariables(editorState);
  } catch (error) {
    console.error('❌ Error converting lexical to plain text:', error);
    throw error;
  }
}

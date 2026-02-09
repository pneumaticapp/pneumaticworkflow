import type { EditorState } from 'lexical';
import { $convertToMarkdownString } from '@lexical/markdown';

import { createLexicalToMarkdownTransformers } from './transformers';



const LEXICAL_MARKDOWN_TRANSFORMERS = createLexicalToMarkdownTransformers();

export function convertLexicalToMarkdown(
  editorState: EditorState,
): string {
  try {

    let result = '';
    editorState.read(() => {
      result = $convertToMarkdownString(LEXICAL_MARKDOWN_TRANSFORMERS);
    });
    return result;
  } catch (error) {
    console.error('❌ Error converting lexical to markdown:', error);
    return '';
  }
}

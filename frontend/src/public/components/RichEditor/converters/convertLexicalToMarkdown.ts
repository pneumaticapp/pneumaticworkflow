import type { EditorState } from 'lexical';
import { $convertToMarkdownString } from '@lexical/markdown';

import { createMarkdownTransformers } from './transformers';

const LEXICAL_MARKDOWN_TRANSFORMERS = createMarkdownTransformers();

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

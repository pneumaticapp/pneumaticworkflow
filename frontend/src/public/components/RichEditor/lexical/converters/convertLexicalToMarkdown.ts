import type { EditorState } from 'lexical';
import {
  $convertToMarkdownString,
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_STAR,
  ITALIC_STAR,
  LINK,
} from '@lexical/markdown';
import type { TConvertLexicalToMarkdownOptions } from './types';

const LEXICAL_MARKDOWN_TRANSFORMERS = [
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_STAR,
  ITALIC_STAR,
  LINK,
];

export function convertLexicalToMarkdown(
  editorState: EditorState,
  options: TConvertLexicalToMarkdownOptions = {},
): string {
  const preserveNewlines = options.preserveNewlines ?? true;
  let result = '';
  editorState.read(() => {
    result = $convertToMarkdownString(
      LEXICAL_MARKDOWN_TRANSFORMERS,
      undefined,
      preserveNewlines,
    );
  });
  return result;
}

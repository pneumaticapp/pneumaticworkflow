import {
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_STAR,
  ITALIC_STAR,
  LINK,
} from '@lexical/markdown';
import { MENTION } from './mentionMarkdown';
import { createVariableTransformer } from './variableMarkdown';
import { CHECKLIST } from './checklistMarkdown';
import type { TTaskVariable } from '../../../TemplateEdit/types';

/**
 * Base markdown transformers without custom ones.
 * Includes standard markdown elements: headings, quotes, lists, formatting, links.
 */
export const BASE_MARKDOWN_TRANSFORMERS = [
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_STAR,
  ITALIC_STAR,
  LINK,
  MENTION,
  CHECKLIST,
];

/**
 * Creates full set of markdown transformers including custom ones.
 * Used for converting markdown to Lexical editor state.
 *
 * @param templateVariables - Optional template variables for variable transformer
 * @returns Array of transformers for markdown parsing
 */
export function createMarkdownTransformers(templateVariables?: TTaskVariable[]) {
  return [
    ...BASE_MARKDOWN_TRANSFORMERS,
    createVariableTransformer(templateVariables),
  ];
}

/**
 * Creates transformers for converting Lexical state to markdown.
 * Similar to createMarkdownTransformers but optimized for export.
 *
 * @returns Array of transformers for markdown export
 */
export function createLexicalToMarkdownTransformers() {
  return [
    ...BASE_MARKDOWN_TRANSFORMERS,
    createVariableTransformer(),
  ];
}
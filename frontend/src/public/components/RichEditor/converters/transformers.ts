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
import { createChecklistTransformer } from './checklistMarkdown';
import { ATTACHMENT, ATTACHMENT_INLINE } from './attachmentMarkdown';
import type { TTaskVariable } from '../../TemplateEdit/types';

/**
 * Transformers for import (markdown → Lexical) and export (Lexical → markdown).
 * Call without args for export.
 *
 * @param templateVariables - Optional: template variables for variable/checklist parsing on import
 */
export function createMarkdownTransformers(templateVariables?: TTaskVariable[]) {
  return [
    ATTACHMENT,
    ATTACHMENT_INLINE,
    HEADING,
    QUOTE,
    UNORDERED_LIST,
    ORDERED_LIST,
    BOLD_STAR,
    ITALIC_STAR,
    LINK,
    MENTION,
    createChecklistTransformer(templateVariables),
    createVariableTransformer(templateVariables),
  ];
}
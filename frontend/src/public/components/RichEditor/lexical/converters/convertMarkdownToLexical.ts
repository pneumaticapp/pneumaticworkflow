import type { LexicalEditor } from 'lexical';
import { $getRoot } from 'lexical';
import {
  $convertFromMarkdownString,
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_STAR,
  ITALIC_STAR,
  LINK,
} from '@lexical/markdown';
import { prepareChecklistsForRendering } from '../../../../utils/checklists/prepareChecklistsForRendering';

const LEXICAL_MARKDOWN_TRANSFORMERS = [
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_STAR,
  ITALIC_STAR,
  LINK,
];

export function getInitialLexicalState(markdown: string): string {
  return prepareChecklistsForRendering(markdown);
}

export function applyMarkdownToEditor(
  editor: LexicalEditor,
  markdown: string,
  options: { tag?: string } = {},
): void {
  const prepared = getInitialLexicalState(markdown);
  editor.update(
    () => {
      const root = $getRoot();
      root.clear();
      $convertFromMarkdownString(
        prepared,
        LEXICAL_MARKDOWN_TRANSFORMERS,
        root,
        true,
      );
    },
    { tag: options.tag ?? 'history-merge' },
  );
}

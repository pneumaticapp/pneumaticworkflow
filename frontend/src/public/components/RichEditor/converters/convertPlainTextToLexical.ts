import type { LexicalEditor } from 'lexical';
import { $createParagraphNode, $getRoot } from 'lexical';

import { parseTextWithVariables, removeUnknownVariableTokens } from './variableMarkdown';
import type { TTaskVariable } from '../../TemplateEdit/types';



const PLAIN_TEXT_PARSE_OPTIONS = {
  variablesOnly: true,
} as const;

export function applyPlainTextToEditor(
  editor: LexicalEditor,
  text: string,
  options: { tag?: string; templateVariables?: TTaskVariable[] } = {},
): void {
  try {
    editor.update(
      () => {
        const root = $getRoot();
        root.clear();
        const paragraph = $createParagraphNode();
        const preparedText = removeUnknownVariableTokens(text, options.templateVariables);

        if (preparedText.trim() !== '') {
          const nodes = parseTextWithVariables(preparedText, options.templateVariables, PLAIN_TEXT_PARSE_OPTIONS);
          nodes.forEach((node) => paragraph.append(node));
        }

        root.append(paragraph);
      },
      { tag: options.tag ?? 'history-merge' },
    );
  } catch (error) {
    console.error('❌ Error loading plain text into editor:', error);
  }
}

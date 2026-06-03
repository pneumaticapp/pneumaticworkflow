import { useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  COMMAND_PRIORITY_HIGH,
  PASTE_COMMAND,
} from 'lexical';

import { parseTextWithVariables, removeUnknownVariableTokens } from '../../converters/variableMarkdown';
import type { TTaskVariable } from '../../../TemplateEdit/types';



const PLAIN_TEXT_PARSE_OPTIONS = {
  variablesOnly: true,
} as const;

export interface IPlainTextPastePluginProps {
  templateVariables?: TTaskVariable[];
}

export function PlainTextPastePlugin({ templateVariables }: IPlainTextPastePluginProps): null {
  const [editor] = useLexicalComposerContext();
  const templateVariablesRef = useRef(templateVariables);
  templateVariablesRef.current = templateVariables;

  useEffect(() => {
    return editor.registerCommand(
      PASTE_COMMAND,
      (event: ClipboardEvent) => {
        const plainText = event.clipboardData?.getData('text/plain');
        if (plainText == null) return false;

        event.preventDefault();
        editor.update(() => {
          const selection = $getSelection();
          if (!$isRangeSelection(selection)) return;

          const preparedText = removeUnknownVariableTokens(
            plainText,
            templateVariablesRef.current,
          );

          if (preparedText.trim() === '') {
            if (!selection.isCollapsed()) {
              selection.removeText();
            }
            return;
          }

          const nodes = parseTextWithVariables(
            preparedText,
            templateVariablesRef.current,
            PLAIN_TEXT_PARSE_OPTIONS,
          );

          selection.insertNodes(nodes);
        });

        return true;
      },
      COMMAND_PRIORITY_HIGH,
    );
  }, [editor]);

  return null;
}

import { useCallback } from 'react';
import { TOGGLE_LINK_COMMAND } from '@lexical/link';
import {
  LexicalEditor,
  $getSelection,
  $isRangeSelection,
  $createTextNode,
  $createRangeSelection,
  $setSelection,
} from 'lexical';



export function useLinkActions(editor: LexicalEditor, onFormClose: () => void) {
  const applyLink = useCallback(
    (url: string, linkText?: string) => {
      if (linkText != null && linkText.trim() !== '') {
        insertTextAndApplyLink(editor, linkText.trim(), url);
      } else {
        editor.dispatchCommand(TOGGLE_LINK_COMMAND, url);
      }
      onFormClose();
    },
    [editor, onFormClose],
  );

  return { applyLink };
}

function insertTextAndApplyLink(editor: LexicalEditor, text: string, url: string): void {
  editor.update(() => {
    const selection = $getSelection();
    if (!$isRangeSelection(selection)) return;

    const textNode = $createTextNode(text);
    selection.insertNodes([textNode]);

    const rangeSelection = $createRangeSelection();
    rangeSelection.anchor.set(textNode.getKey(), 0, 'text');
    rangeSelection.focus.set(textNode.getKey(), text.length, 'text');
    $setSelection(rangeSelection);

    editor.dispatchCommand(TOGGLE_LINK_COMMAND, url);
  });
}
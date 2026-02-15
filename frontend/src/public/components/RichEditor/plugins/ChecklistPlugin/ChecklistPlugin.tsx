import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  COMMAND_PRIORITY_HIGH,
  COMMAND_PRIORITY_LOW,
  COMMAND_PRIORITY_NORMAL,
  KEY_BACKSPACE_COMMAND,
  KEY_ENTER_COMMAND,
  SELECTION_INSERT_CLIPBOARD_NODES_COMMAND,
} from 'lexical';
import {
  createBackspaceHandler,
  createEnterKeyHandler,
  createInsertChecklistHandler,
  createPasteClipboardNodesHandler,
} from './checklistPluginHandlers';
import { INSERT_CHECKLIST_COMMAND } from './insertChecklistCommand';

export function ChecklistPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      KEY_ENTER_COMMAND,
      createEnterKeyHandler(editor),
      COMMAND_PRIORITY_HIGH,
    );
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      INSERT_CHECKLIST_COMMAND,
      createInsertChecklistHandler(editor),
      COMMAND_PRIORITY_LOW,
    );
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      KEY_BACKSPACE_COMMAND,
      createBackspaceHandler(editor),
      COMMAND_PRIORITY_NORMAL,
    );
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      SELECTION_INSERT_CLIPBOARD_NODES_COMMAND,
      createPasteClipboardNodesHandler(),
      COMMAND_PRIORITY_HIGH,
    );
  }, [editor]);

  return null;
}

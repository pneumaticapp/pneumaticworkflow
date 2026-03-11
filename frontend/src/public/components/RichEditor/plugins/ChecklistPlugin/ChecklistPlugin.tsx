import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  COMMAND_PRIORITY_HIGH,
  COMMAND_PRIORITY_LOW,
  KEY_BACKSPACE_COMMAND,
  KEY_DELETE_COMMAND,
  KEY_ENTER_COMMAND,
  SELECTION_INSERT_CLIPBOARD_NODES_COMMAND,
} from 'lexical';
import {
  createBackspaceHandler,
  createDeleteHandler,
  createEnterKeyHandler,
  createInsertChecklistHandler,
  createConvertChecklistToListHandler,
  createPasteClipboardNodesHandler,
} from './checklistPluginHandlers';
import { CONVERT_CHECKLIST_TO_LIST_COMMAND, INSERT_CHECKLIST_COMMAND } from './insertChecklistCommand';

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
      CONVERT_CHECKLIST_TO_LIST_COMMAND,
      createConvertChecklistToListHandler(editor),
      COMMAND_PRIORITY_LOW,
    );
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      KEY_BACKSPACE_COMMAND,
      createBackspaceHandler(editor),
      COMMAND_PRIORITY_HIGH,
    );
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      KEY_DELETE_COMMAND,
      createDeleteHandler(editor),
      COMMAND_PRIORITY_HIGH,
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

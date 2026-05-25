import type { LexicalCommand } from 'lexical';
import { createCommand } from 'lexical';

export const INSERT_CHECKLIST_COMMAND: LexicalCommand<void> = createCommand('INSERT_CHECKLIST_COMMAND');

export type ConvertChecklistToListPayload = 'number' | 'bullet';
export const CONVERT_CHECKLIST_TO_LIST_COMMAND: LexicalCommand<ConvertChecklistToListPayload> =
  createCommand('CONVERT_CHECKLIST_TO_LIST_COMMAND');

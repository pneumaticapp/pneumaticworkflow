import type { LexicalCommand } from 'lexical';
import { createCommand } from 'lexical';

export const INSERT_CHECKLIST_COMMAND: LexicalCommand<void> = createCommand('INSERT_CHECKLIST_COMMAND');

import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListNode, ListItemNode } from '@lexical/list';
import { LinkNode } from '@lexical/link';
import {
  ImageAttachmentNode,
  VideoAttachmentNode,
  FileAttachmentNode,
} from './attachments';
import { MentionNode } from './MentionNode';
import { VariableNode } from './VariableNode';
import { ChecklistNode } from './ChecklistNode';
import { ChecklistItemNode } from './ChecklistItemNode';

export const LEXICAL_NODES = [
  HeadingNode,
  QuoteNode,
  ListNode,
  ListItemNode,
  LinkNode,
  ImageAttachmentNode,
  VideoAttachmentNode,
  FileAttachmentNode,
  MentionNode,
  VariableNode,
  ChecklistNode,
  ChecklistItemNode,
];

export {
  CHECKBOX_CLASS,
  CHECKLIST_ITEM_CLASS,
  ChecklistItemNode,
  $createChecklistItemNode,
  $isChecklistItemNode,
} from './ChecklistItemNode';
export type { SerializedChecklistItemNode, TChecklistItemNodePayload } from './ChecklistItemNode';

export {
  ChecklistNode,
  $createChecklistNode,
  $isChecklistNode,
} from './ChecklistNode';
export type { SerializedChecklistNode, TChecklistNodePayload } from './ChecklistNode';

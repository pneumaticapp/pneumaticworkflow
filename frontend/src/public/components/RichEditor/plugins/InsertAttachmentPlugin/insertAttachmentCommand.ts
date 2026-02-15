import { createCommand } from 'lexical';
import type { TAttachmentPayload } from '../../nodes/attachments/types';

export type TInsertAttachmentPayload = TAttachmentPayload & {
  type: 'image' | 'video' | 'file';
};

export const INSERT_ATTACHMENT_COMMAND = createCommand<TInsertAttachmentPayload>();

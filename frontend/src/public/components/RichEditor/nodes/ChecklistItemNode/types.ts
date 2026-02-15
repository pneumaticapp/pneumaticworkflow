import type { SerializedElementNode } from 'lexical';

export type SerializedChecklistItemNode = Omit<SerializedElementNode, 'type' | 'version'> & {
  type: 'checklist-item';
  version: 1;
  listApiName: string;
  itemApiName: string;
};

export type TChecklistItemNodePayload = {
  listApiName: string;
  itemApiName: string;
};

import type { SerializedElementNode } from 'lexical';

export type SerializedChecklistNode = Omit<SerializedElementNode, 'type' | 'version'> & {
  type: 'checklist';
  version: 1;
  listApiName: string;
};

export type TChecklistNodePayload = {
  listApiName: string;
};

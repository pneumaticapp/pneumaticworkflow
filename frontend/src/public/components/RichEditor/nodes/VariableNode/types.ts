import type { SerializedLexicalNode } from 'lexical';

export type SerializedVariableNode = SerializedLexicalNode & {
  type: 'variable';
  version: 1;
  apiName: string;
  title: string;
  subtitle?: string;
};

export type TVariableNodePayload = {
  apiName: string;
  title?: string;
  subtitle?: string;
};

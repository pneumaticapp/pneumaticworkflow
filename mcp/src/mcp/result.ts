import type { CallToolResult } from '@modelcontextprotocol/server';

import { boundEnvelope, type Json } from '../presenters/index.js';
import { publicError, toConnectorError } from './errors.js';

type Content = CallToolResult['content'][number];

export interface ToolOutput {
  data: Json;
  truncated?: boolean;
  content?: Content[];
}

export function success({ data, truncated = false, content = [] }: ToolOutput): CallToolResult {
  const envelope = boundEnvelope({ data, truncated });
  return {
    content: [{ type: 'text', text: JSON.stringify(envelope) }, ...content],
    structuredContent: { ...envelope },
  };
}

export function failure(error: unknown, write: boolean): CallToolResult {
  const body = { error: publicError(toConnectorError(error), write) };
  return {
    content: [{ type: 'text', text: JSON.stringify(body) }],
    structuredContent: body,
    isError: true,
  };
}

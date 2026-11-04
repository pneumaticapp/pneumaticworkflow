import {
  CLIENT_CAPABILITIES_META_KEY,
  inputRequired,
  inputResponse,
  type CallToolResult,
  type ClientCapabilities,
  type InputRequiredResult,
  type McpServer,
  type ServerContext,
  type StandardSchemaWithJSON,
  type ToolAnnotations,
  type ToolCallback,
} from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { log } from '../core/log.js';
import { count } from '../core/metrics.js';
import type { RemoteFetcher, UploadLinks } from '../core/ports.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { failure, success, type ToolOutput } from './result.js';

export interface ToolContext {
  client: PneumaticClient;
  fetchRemote: RemoteFetcher;
  uploads?: UploadLinks;
}

type Capability = 'uploads';

export const TOOLSETS = ['core', 'files', 'design', 'analytics', 'admin'] as const;
export type Toolset = (typeof TOOLSETS)[number];

interface ToolConfig<Schema> {
  title: string;
  description: string;
  inputSchema: Schema;
  annotations: ToolAnnotations;
  requires?: Capability;
  pairedWith?: string;
}

export interface ToolDef extends ToolConfig<z.ZodObject> {
  name: string;
  // Set from the module's group in src/tools/index.ts.
  toolset?: Toolset;
  run(args: z.output<z.ZodObject>, context: ToolContext): Promise<ToolOutput>;
}

export function tool<Schema extends z.ZodObject & StandardSchemaWithJSON>(
  name: string,
  config: ToolConfig<Schema>,
  run: (args: z.output<Schema>, context: ToolContext) => Promise<ToolOutput>,
): ToolDef {
  return { name, ...config, run };
}

export interface ToolSelection {
  toolsets?: readonly Toolset[];
  readOnly?: boolean;
}

export function availableTools(
  tools: readonly ToolDef[],
  context: ToolContext,
  { toolsets, readOnly = false }: ToolSelection = {},
): ToolDef[] {
  const offered = tools.filter(
    (definition) =>
      (!definition.requires || context[definition.requires] !== undefined) &&
      (!toolsets || toolsets.includes(definition.toolset ?? 'core')) &&
      (!readOnly || definition.annotations.readOnlyHint === true),
  );
  const names = new Set(offered.map(({ name }) => name));
  return offered.filter(({ pairedWith }) => !pairedWith || names.has(pairedWith));
}

const CONFIRM_KEY = 'confirm';
const confirmation = z.object({ confirm: z.boolean().default(true).describe('Allow this change') });

function supportsForms(server: McpServer, context: ServerContext): boolean {
  const envelope = context.mcpReq.envelope as Record<string, unknown> | undefined;
  const capabilities = (envelope?.[CLIENT_CAPABILITIES_META_KEY] ?? server.server.getClientCapabilities()) as
    | ClientCapabilities
    | undefined;
  return Boolean(capabilities?.elicitation);
}

function describeCall(title: string, args: unknown): string {
  const details = Object.entries((args ?? {}) as Record<string, unknown>)
    .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
    .join(', ')
    .slice(0, 500);
  return `${title}${details ? ` (${details})` : ''}. This cannot be undone easily. Continue?`;
}

// Clients that can show forms confirm destructive calls themselves; others rely on the instructions.
function confirmDestructive(
  server: McpServer,
  request: ServerContext,
  title: string,
  args: unknown,
): InputRequiredResult | CallToolResult | undefined {
  if (!supportsForms(server, request)) {
    return undefined;
  }
  const answer = inputResponse(request.mcpReq.inputResponses, CONFIRM_KEY);
  if (answer.kind !== 'elicit') {
    return inputRequired({
      inputRequests: {
        [CONFIRM_KEY]: inputRequired.elicit({
          message: describeCall(title, args),
          requestedSchema: confirmation,
        }),
      },
    });
  }
  // Accepting the form confirms unless the user explicitly unticked the box.
  if (answer.action !== 'accept' || answer.content?.confirm === false) {
    return failure(new ConnectorError('cancelled'), false);
  }
  return undefined;
}

function recordToolCall(name: string, result: InputRequiredResult | CallToolResult, startedMs: number) {
  const error = (result.structuredContent as { error?: { code?: string } } | undefined)?.error;
  const outcome = 'inputRequests' in result ? 'confirmation_requested' : (error?.code ?? 'ok');
  const seconds = (performance.now() - startedMs) / 1000;
  count('mcp_tool_calls_total', 'MCP tool calls by tool and outcome', { tool: name, outcome });
  count('mcp_tool_call_seconds_total', 'Total MCP tool call time in seconds', { tool: name }, seconds);
  log(error && error.code !== 'cancelled' ? 'warn' : 'info', 'tool_call', {
    tool: name,
    outcome,
    ms: Math.round(seconds * 1000),
  });
}

export function registerTools(server: McpServer, tools: readonly ToolDef[], context: ToolContext) {
  for (const { name, title, description, inputSchema, annotations, run } of tools) {
    const write = annotations.readOnlyHint !== true;
    const handle = async (args: unknown, request: ServerContext) => {
      const pending = annotations.destructiveHint ? confirmDestructive(server, request, title, args) : undefined;
      if (pending) {
        return pending;
      }
      try {
        return success(await run(args as never, context));
      } catch (error) {
        return failure(error, write);
      }
    };
    const callback = async (args: unknown, request: ServerContext) => {
      const started = performance.now();
      const result = await handle(args, request);
      recordToolCall(name, result, started);
      return result;
    };
    server.registerTool(
      name,
      { title, description, inputSchema, annotations } as { inputSchema: z.ZodObject & StandardSchemaWithJSON },
      callback as ToolCallback<z.ZodObject & StandardSchemaWithJSON>,
    );
  }
}

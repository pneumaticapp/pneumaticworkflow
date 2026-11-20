import { McpServer } from '@modelcontextprotocol/server';

import type { RemoteFetcher, UploadLinks } from './core/ports.js';
import { VERSION } from './core/version.js';
import { buildInstructions } from './mcp/instructions.js';
import { registerPrompts } from './mcp/prompts.js';
import { availableTools, registerTools, type ToolContext, type ToolSelection } from './mcp/toolDef.js';
import type { PneumaticClient } from './pneumatic/client.js';
import { fetchRemoteFile } from './pneumatic/remoteFile.js';
import { allTools } from './tools/index.js';

const SERVER_NAME = 'pneumatic';

export interface ServerOptions extends ToolSelection {
  fetchRemote?: RemoteFetcher;
  uploads?: UploadLinks;
}

export function buildServer(
  client: PneumaticClient,
  { fetchRemote = fetchRemoteFile, uploads, ...selection }: ServerOptions = {},
): McpServer {
  const context: ToolContext = { client, fetchRemote, uploads };
  const tools = availableTools(allTools, context, selection);
  const server = new McpServer(
    { name: SERVER_NAME, title: 'Pneumatic Workflow', version: VERSION },
    { instructions: buildInstructions(tools) },
  );
  registerTools(server, tools, context);
  registerPrompts(server, new Set(tools.map(({ name }) => name)));
  return server;
}

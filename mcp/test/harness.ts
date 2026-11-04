import { Client, InMemoryTransport } from '@modelcontextprotocol/client';

import { createPneumaticClient } from '../src/pneumatic/client.js';
import { buildServer, type ServerOptions } from '../src/server.js';
import { VALID_API_KEY, type createFakePneumatic } from './fakePneumatic.js';

type FakePneumatic = ReturnType<typeof createFakePneumatic>;

export interface ConnectOptions extends ServerOptions {
  appUrl?: string;
  fetchFn?: typeof fetch;
  // false leaves PNEUMATIC_FILES_URL unset.
  storage?: boolean;
  filesInternalUrl?: string;
  capabilities?: Record<string, unknown>;
}

export async function connectServer(
  fake: FakePneumatic,
  {
    appUrl,
    fetchFn = fake.fetchFn,
    storage = true,
    filesInternalUrl,
    capabilities = {},
    ...options
  }: ConnectOptions = {},
): Promise<Client> {
  const pneumatic = createPneumaticClient(
    { apiUrl: fake.apiUrl, filesUrl: storage ? fake.filesUrl : undefined, filesInternalUrl, appUrl, fetchFn },
    VALID_API_KEY,
  );
  const server = buildServer(pneumatic, options);
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: 'test', version: '1.0.0' }, { capabilities });
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  return client;
}

export async function callTool(client: Client, name: string, args: Record<string, unknown> = {}) {
  const result = await client.callTool({ name, arguments: args });
  const content = result.content as Array<{ type: string; text?: string; [key: string]: unknown }>;
  return {
    isError: Boolean(result.isError),
    text: content[0]?.text ?? '',
    content,
    ...(result.structuredContent as { data?: any; truncated?: boolean; error?: any }),
  };
}

export function lastBody(fake: FakePneumatic, path: string, method?: string): any {
  return fake.requests.filter((request) => request.path === path && (!method || request.method === method)).at(-1)
    ?.body;
}

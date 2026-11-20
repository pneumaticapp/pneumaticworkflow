import { randomBytes } from 'node:crypto';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import {
  Client,
  discoverAuthorizationServerMetadata,
  StreamableHTTPClientTransport,
} from '@modelcontextprotocol/client';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { loadConfig } from '../src/config.js';
import { createHttpApp } from '../src/http/app.js';
import { s256 } from '../src/http/oauthTokens.js';
import { createEntryProxy } from './entryProxy.js';
import { createFakePneumatic, VALID_API_KEY } from './fakePneumatic.js';

const fake = createFakePneumatic();
const directory = mkdtempSync(join(tmpdir(), 'pneumatic-entry-'));
const upstream = createServer();
const receivedPaths: string[] = [];
let proxy: ReturnType<typeof createEntryProxy>;
let baseUrl: string;

beforeAll(async () => {
  await new Promise<void>((resolve) => upstream.listen(0, '127.0.0.1', resolve));
  const upstreamPort = (upstream.address() as AddressInfo).port;
  proxy = createEntryProxy(`http://127.0.0.1:${upstreamPort}`);
  await new Promise<void>((resolve) => proxy.listen(0, '127.0.0.1', resolve));
  baseUrl = `http://127.0.0.1:${(proxy.address() as AddressInfo).port}`;
  const replayFile = join(directory, 'replay.json');
  writeFileSync(replayFile, '');
  const config = loadConfig(['--http'], {
    BACKEND_PRIVATE_URL: fake.apiUrl,
    PNEUMATIC_FILES_URL: fake.filesUrl,
    PUBLIC_URL: baseUrl,
    PORT: String(upstreamPort),
    TOKEN_SECRET: randomBytes(32).toString('hex'),
    OAUTH_REPLAY_FILE: replayFile,
    RATE_LIMIT_PER_MINUTE: '0',
    TRUST_PROXY: 'false',
  });
  if (config.transport !== 'http') throw new Error('HTTP configuration expected');
  const app = createHttpApp(config, fake.fetchFn);
  upstream.on('request', (req, res) => {
    receivedPaths.push(req.url ?? '/');
    app(req, res);
  });
});

afterAll(async () => {
  if (proxy?.listening) await new Promise<void>((resolve) => proxy.close(() => resolve()));
  if (upstream.listening) await new Promise<void>((resolve) => upstream.close(() => resolve()));
  rmSync(directory, { recursive: true, force: true });
});

function form(values: Record<string, string>) {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(values),
  };
}

async function connect(token: string) {
  const client = new Client({ name: 'entry-test', version: '1.0.0' });
  await client.connect(
    new StreamableHTTPClientTransport(new URL(`${baseUrl}/mcp`), {
      requestInit: { headers: { Authorization: `Bearer ${token}` } },
    }),
  );
  return client;
}

describe('public MCP entry', () => {
  it('discovers OAuth through standard public URLs and the namespaced upstream', async () => {
    const response = await fetch(`${baseUrl}/mcp`);
    expect(response.status).toBe(401);
    const metadataUrl = /resource_metadata="([^"]+)"/.exec(response.headers.get('www-authenticate')!)![1]!;
    expect(metadataUrl).toBe(`${baseUrl}/.well-known/oauth-protected-resource/mcp`);
    const resource = (await (await fetch(metadataUrl)).json()) as { authorization_servers: string[] };
    expect(resource).toMatchObject({ resource: `${baseUrl}/mcp`, authorization_servers: [baseUrl] });
    const metadata = await discoverAuthorizationServerMetadata(resource.authorization_servers[0]!);
    expect(metadata).toMatchObject({
      issuer: baseUrl,
      authorization_endpoint: `${baseUrl}/mcp/authorize`,
      token_endpoint: `${baseUrl}/mcp/token`,
      registration_endpoint: `${baseUrl}/mcp/register`,
    });
    expect(receivedPaths).toEqual(
      expect.arrayContaining([
        '/mcp/',
        '/mcp/.well-known/oauth-protected-resource/mcp',
        '/mcp/.well-known/oauth-authorization-server',
      ]),
    );
  });

  it('connects and calls a tool after the public OAuth flow', async () => {
    const metadata = await discoverAuthorizationServerMetadata(baseUrl);
    if (!metadata?.registration_endpoint) throw new Error('OAuth registration endpoint expected');
    const redirectUri = 'https://claude.ai/api/mcp/auth_callback';
    const registration = await fetch(metadata.registration_endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ redirect_uris: [redirectUri], token_endpoint_auth_method: 'none' }),
    });
    expect(registration.status).toBe(201);
    const { client_id: clientId } = (await registration.json()) as { client_id: string };
    const verifier = randomBytes(32).toString('base64url');
    const authorization = await fetch(metadata.authorization_endpoint, {
      ...form({
        response_type: 'code',
        client_id: clientId,
        redirect_uri: redirectUri,
        code_challenge: s256(verifier),
        code_challenge_method: 'S256',
        api_key: VALID_API_KEY,
      }),
      redirect: 'manual',
    });
    expect(authorization.status).toBe(302);
    const callback = new URL(authorization.headers.get('location')!);
    expect(callback.searchParams.get('iss')).toBe(baseUrl);
    const exchange = await fetch(
      metadata.token_endpoint,
      form({
        grant_type: 'authorization_code',
        client_id: clientId,
        redirect_uri: redirectUri,
        code: callback.searchParams.get('code')!,
        code_verifier: verifier,
      }),
    );
    expect(exchange.status).toBe(200);
    const { access_token: token } = (await exchange.json()) as { access_token: string };
    const client = await connect(token);
    try {
      expect((await client.listTools()).tools.map(({ name }) => name)).toContain('get_current_user');
      const result = await client.callTool({ name: 'get_current_user', arguments: {} });
      expect(result.isError).toBeFalsy();
      expect(result.structuredContent).toMatchObject({ data: { id: 7 } });
    } finally {
      await client.close();
    }
  });

  it('preserves queries and keeps unrelated paths outside the MCP upstream', async () => {
    const response = await fetch(`${baseUrl}/.well-known/oauth-protected-resource/mcp?client=a%2Fb`);
    expect(response.status).toBe(200);
    expect(receivedPaths.at(-1)).toBe('/mcp/.well-known/oauth-protected-resource/mcp?client=a%2Fb');
    const count = receivedPaths.length;
    for (const path of ['/mcpx', '/mcp-other', '/auth/signup/', '/.well-known/acme-challenge/test']) {
      expect(await (await fetch(`${baseUrl}${path}`)).text()).toBe('frontend');
    }
    expect(receivedPaths).toHaveLength(count);
    expect((await fetch(`${baseUrl}/mcp/unknown`)).status).toBe(404);
    expect(receivedPaths.at(-1)).toBe('/mcp/unknown');
  });

  it('serves a one-time browser upload through the public entry', async () => {
    const client = await connect(VALID_API_KEY);
    try {
      const created = await client.callTool({ name: 'create_upload_link', arguments: { filename: 'sample.txt' } });
      const { uploadUrl, uploadId } = (created.structuredContent as { data: { uploadUrl: string; uploadId: string } })
        .data;
      expect(uploadUrl.startsWith(`${baseUrl}/mcp/upload/`)).toBe(true);
      expect((await fetch(uploadUrl)).status).toBe(200);
      const body = new FormData();
      body.append('file', new Blob(['sample content'], { type: 'text/plain' }), 'sample.txt');
      expect((await fetch(uploadUrl, { method: 'POST', headers: { Origin: baseUrl }, body })).status).toBe(200);
      const status = await client.callTool({ name: 'get_upload_status', arguments: { uploadId } });
      expect(status.structuredContent).toMatchObject({ data: { status: 'ready', file: { size: 14 } } });
      expect((await fetch(uploadUrl)).status).toBe(404);
    } finally {
      await client.close();
    }
  });
});

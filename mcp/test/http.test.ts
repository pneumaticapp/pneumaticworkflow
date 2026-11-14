import { randomBytes } from 'node:crypto';
import { mkdirSync, mkdtempSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';
import type { ErrorRequestHandler } from 'express';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';

import { loadConfig, type HttpConfig } from '../src/config.js';
import { createHttpApp } from '../src/http/app.js';
import { s256 } from '../src/http/oauthTokens.js';
import { createSealer } from '../src/http/sealer.js';
import { createFileReplayStore } from '../src/stores/fileReplayStore.js';
import { createMemoryUploadStore } from '../src/stores/memoryUploadStore.js';
import { delayed } from './delayed.js';
import { createFakePneumatic, VALID_API_KEY } from './fakePneumatic.js';

const REDIRECT_URI = 'https://claude.ai/api/mcp/auth_callback';
const tokenSecret = randomBytes(32).toString('hex');
const replayDirectory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));

let server: Server;
let baseUrl: string;
const fake = createFakePneumatic();

beforeAll(async () => {
  server = createServer();
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address() as AddressInfo;
  baseUrl = `http://127.0.0.1:${port}`;
  writeFileSync(join(replayDirectory, 'used.json'), '');
  const config = loadConfig(['--http'], {
    PNEUMATIC_API_URL: fake.apiUrl,
    PNEUMATIC_FILES_URL: fake.filesUrl,
    HOST: '127.0.0.1',
    PORT: String(port),
    PUBLIC_URL: baseUrl,
    TOKEN_SECRET: tokenSecret,
    OAUTH_REPLAY_FILE: join(replayDirectory, 'used.json'),
    RATE_LIMIT_PER_MINUTE: '0',
    TRUST_PROXY: 'false',
  });
  if (config.transport !== 'http') {
    throw new Error('HTTP configuration expected');
  }
  server.on('request', createHttpApp(config, fake.fetchFn));
});

afterAll(async () => {
  await new Promise((resolve) => server.close(resolve));
  rmSync(replayDirectory, { recursive: true, force: true });
});

function form(values: Record<string, string>) {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(values),
  };
}

async function register(body: Record<string, unknown> = {}, url = baseUrl) {
  const response = await fetch(`${url}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_name: 'Claude', redirect_uris: [REDIRECT_URI], ...body }),
  });
  return { status: response.status, body: (await response.json()) as Record<string, string> };
}

async function authorize(clientId: string, verifier: string, apiKey = VALID_API_KEY, url = baseUrl) {
  const params = {
    response_type: 'code',
    client_id: clientId,
    redirect_uri: REDIRECT_URI,
    code_challenge: s256(verifier),
    code_challenge_method: 'S256',
    state: 'xyz',
  };
  return fetch(`${url}/authorize`, { ...form({ ...params, api_key: apiKey }), redirect: 'manual' });
}

async function obtainTokens() {
  const { body: client } = await register();
  const verifier = randomBytes(32).toString('base64url');
  const redirect = new URL((await authorize(client.client_id!, verifier)).headers.get('location')!);
  const response = await fetch(
    `${baseUrl}/token`,
    form({
      grant_type: 'authorization_code',
      code: redirect.searchParams.get('code')!,
      code_verifier: verifier,
      client_id: client.client_id!,
      redirect_uri: REDIRECT_URI,
    }),
  );
  return { clientId: client.client_id!, tokens: (await response.json()) as Record<string, string> };
}

async function connect(token: string) {
  const client = new Client({ name: 'test', version: '1.0.0' });
  await client.connect(
    new StreamableHTTPClientTransport(new URL(`${baseUrl}/mcp`), {
      requestInit: { headers: { Authorization: `Bearer ${token}` } },
    }),
  );
  return client;
}

describe('discovery', () => {
  it('challenges unauthenticated MCP requests with resource metadata', async () => {
    const response = await fetch(`${baseUrl}/mcp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
    expect(response.status).toBe(401);
    expect(response.headers.get('www-authenticate')).toContain(
      `resource_metadata="${baseUrl}/.well-known/oauth-protected-resource/mcp"`,
    );
  });

  it('serves protected resource and authorization server metadata', async () => {
    const resource = await (await fetch(`${baseUrl}/.well-known/oauth-protected-resource/mcp`)).json();
    expect(resource).toMatchObject({ resource: `${baseUrl}/mcp`, authorization_servers: [baseUrl] });

    const metadata = await (await fetch(`${baseUrl}/.well-known/oauth-authorization-server`)).json();
    expect(metadata).toMatchObject({
      issuer: baseUrl,
      authorization_endpoint: `${baseUrl}/authorize`,
      token_endpoint: `${baseUrl}/token`,
      registration_endpoint: `${baseUrl}/register`,
      code_challenge_methods_supported: ['S256'],
      authorization_response_iss_parameter_supported: true,
    });
  });
});

describe('client registration', () => {
  it('registers a public client by default', async () => {
    const { status, body } = await register();
    expect(status).toBe(201);
    expect(body.client_id).toMatch(/^pmcp_c_/);
    expect(body.token_endpoint_auth_method).toBe('none');
    expect(body.client_secret).toBeUndefined();
  });

  it('bounds the number and length of redirect URIs', async () => {
    const many = Array.from({ length: 11 }, (_, index) => `https://claude.ai/callback/${index}`);
    expect((await register({ redirect_uris: many })).status).toBe(400);
    expect((await register({ redirect_uris: [`https://claude.ai/${'a'.repeat(2100)}`] })).status).toBe(400);
  });

  it('answers malformed registration JSON with an OAuth error', async () => {
    const response = await fetch(`${baseUrl}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{"redirect_uris":',
    });
    expect(response.status).toBe(400);
    expect(await response.json()).toMatchObject({ error: 'invalid_request' });
  });

  it('rejects redirect hosts outside the allowlist and plain http', async () => {
    expect((await register({ redirect_uris: ['https://evil.example/cb'] })).status).toBe(400);
    expect((await register({ redirect_uris: ['http://claude.ai/cb'] })).status).toBe(400);
    expect((await register({ redirect_uris: ['http://localhost:6274/callback'] })).status).toBe(201);
    expect((await register({ redirect_uris: ['https://attacker@claude.ai/cb'] })).status).toBe(400);
  });
});

describe('authorization flow', () => {
  it.each(['https://www.cursor.com/agents/mcp/oauth/callback', 'http://localhost:8787/callback'])(
    'connects Cursor through OAuth using its callback %s',
    async (redirectUri) => {
      const { status, body: registration } = await register({ client_name: 'Cursor', redirect_uris: [redirectUri] });
      expect(status).toBe(201);
      const verifier = randomBytes(32).toString('base64url');
      const authorization = await fetch(`${baseUrl}/authorize`, {
        ...form({
          response_type: 'code',
          client_id: registration.client_id!,
          redirect_uri: redirectUri,
          code_challenge: s256(verifier),
          code_challenge_method: 'S256',
          api_key: VALID_API_KEY,
        }),
        redirect: 'manual',
      });
      expect(authorization.status).toBe(302);
      const callback = new URL(authorization.headers.get('location')!);
      expect(`${callback.origin}${callback.pathname}`).toBe(redirectUri);
      const exchange = await fetch(
        `${baseUrl}/token`,
        form({
          grant_type: 'authorization_code',
          client_id: registration.client_id!,
          redirect_uri: redirectUri,
          code: callback.searchParams.get('code')!,
          code_verifier: verifier,
        }),
      );
      expect(exchange.status).toBe(200);
      const tokens = (await exchange.json()) as { access_token: string };
      const client = await connect(tokens.access_token);
      try {
        expect((await client.listTools()).tools.map(({ name }) => name)).toContain('get_current_user');
      } finally {
        await client.close();
      }
    },
  );

  it('renders the consent page with the client name and escapes input', async () => {
    const { body: client } = await register({ client_name: '<script>x</script>' });
    const query = new URLSearchParams({
      response_type: 'code',
      client_id: client.client_id!,
      redirect_uri: REDIRECT_URI,
      code_challenge: s256('v'.repeat(43)),
      code_challenge_method: 'S256',
    });
    const response = await fetch(`${baseUrl}/authorize?${query}`);
    const html = await response.text();
    expect(response.status).toBe(200);
    expect(response.headers.get('x-frame-options')).toBe('DENY');
    expect(html).toContain('&lt;script&gt;x&lt;/script&gt;');
    expect(html).toContain('claude.ai');
  });

  it('refuses unregistered redirect URIs without redirecting', async () => {
    const { body: client } = await register();
    const query = new URLSearchParams({
      response_type: 'code',
      client_id: client.client_id!,
      redirect_uri: 'https://claude.ai/other',
      code_challenge: s256('verifier'),
      code_challenge_method: 'S256',
    });
    const response = await fetch(`${baseUrl}/authorize?${query}`, { redirect: 'manual' });
    expect(response.status).toBe(400);
  });

  it('requires PKCE S256', async () => {
    const { body: client } = await register();
    const query = new URLSearchParams({
      response_type: 'code',
      client_id: client.client_id!,
      redirect_uri: REDIRECT_URI,
    });
    const response = await fetch(`${baseUrl}/authorize?${query}`, { redirect: 'manual' });
    expect(response.status).toBe(302);
    expect(new URL(response.headers.get('location')!).searchParams.get('error')).toBe('invalid_request');
  });

  it('rejects malformed PKCE challenges', async () => {
    const { body: client } = await register();
    const query = new URLSearchParams({
      response_type: 'code',
      client_id: client.client_id!,
      redirect_uri: REDIRECT_URI,
      code_challenge: 'short',
      code_challenge_method: 'S256',
    });
    const response = await fetch(`${baseUrl}/authorize?${query}`, { redirect: 'manual' });
    expect(new URL(response.headers.get('location')!).searchParams.get('error')).toBe('invalid_request');
  });

  it('rejects unsupported scopes instead of issuing the full scope', async () => {
    const { body: client } = await register();
    const requestsBefore = fake.requests.length;
    const response = await fetch(`${baseUrl}/authorize`, {
      ...form({
        response_type: 'code',
        client_id: client.client_id!,
        redirect_uri: REDIRECT_URI,
        code_challenge: s256('v'.repeat(43)),
        code_challenge_method: 'S256',
        scope: 'read-only',
        api_key: VALID_API_KEY,
      }),
      redirect: 'manual',
    });
    expect(response.status).toBe(302);
    expect(new URL(response.headers.get('location')!).searchParams.get('error')).toBe('invalid_scope');
    expect(fake.requests).toHaveLength(requestsBefore);
  });

  it('rejects a short verifier even if its hash matches the challenge', async () => {
    const { body: client } = await register();
    const verifier = 'short-verifier';
    const redirect = new URL((await authorize(client.client_id!, verifier)).headers.get('location')!);
    const response = await fetch(
      `${baseUrl}/token`,
      form({
        grant_type: 'authorization_code',
        code: redirect.searchParams.get('code')!,
        code_verifier: verifier,
        client_id: client.client_id!,
        redirect_uri: REDIRECT_URI,
      }),
    );
    expect(response.status).toBe(400);
    expect(await response.json()).toMatchObject({ error: 'invalid_grant' });
  });

  it('shows an error for an API key rejected by Pneumatic', async () => {
    const { body: client } = await register();
    const response = await authorize(client.client_id!, 'v'.repeat(43), 'pn-wrong');
    expect(response.status).toBe(400);
    expect(await response.text()).toContain('rejected by Pneumatic');
  });

  it('issues tokens for a valid key and rejects code reuse or a wrong verifier', async () => {
    const { body: client } = await register();
    const verifier = randomBytes(32).toString('base64url');
    const response = await authorize(client.client_id!, verifier);
    expect(response.status).toBe(302);
    const location = new URL(response.headers.get('location')!);
    expect(`${location.origin}${location.pathname}`).toBe(REDIRECT_URI);
    expect(location.searchParams.get('state')).toBe('xyz');
    const code = location.searchParams.get('code')!;

    const exchange = (codeVerifier: string) =>
      fetch(
        `${baseUrl}/token`,
        form({
          grant_type: 'authorization_code',
          code,
          code_verifier: codeVerifier,
          client_id: client.client_id!,
          redirect_uri: REDIRECT_URI,
        }),
      );

    expect((await exchange('wrong-verifier')).status).toBe(400);
    const success = await exchange(verifier);
    expect(success.status).toBe(200);
    expect(await success.json()).toMatchObject({ token_type: 'Bearer', expires_in: 3600 });
    const reuse = await exchange(verifier);
    expect(await reuse.json()).toMatchObject({ error: 'invalid_grant' });
  });

  it('requires the redirect URI at token exchange when it was supplied at authorization', async () => {
    const { body: client } = await register();
    const verifier = randomBytes(32).toString('base64url');
    const redirect = new URL((await authorize(client.client_id!, verifier)).headers.get('location')!);
    const values = {
      grant_type: 'authorization_code',
      code: redirect.searchParams.get('code')!,
      code_verifier: verifier,
      client_id: client.client_id!,
    };
    expect((await fetch(`${baseUrl}/token`, form(values))).status).toBe(400);
    expect((await fetch(`${baseUrl}/token`, form({ ...values, redirect_uri: REDIRECT_URI }))).status).toBe(200);
  });

  it('permits omitting the redirect URI at exchange when it was inferred at authorization', async () => {
    const { body: client } = await register();
    const verifier = randomBytes(32).toString('base64url');
    const query = new URLSearchParams({
      response_type: 'code',
      client_id: client.client_id!,
      code_challenge: s256(verifier),
      code_challenge_method: 'S256',
    });
    const page = await fetch(`${baseUrl}/authorize?${query}`);
    expect(await page.text()).not.toContain('name="redirect_uri"');
    const redirect = new URL(
      (
        await fetch(`${baseUrl}/authorize`, {
          ...form({ ...Object.fromEntries(query), api_key: VALID_API_KEY }),
          redirect: 'manual',
        })
      ).headers.get('location')!,
    );
    const response = await fetch(
      `${baseUrl}/token`,
      form({
        grant_type: 'authorization_code',
        code: redirect.searchParams.get('code')!,
        code_verifier: verifier,
        client_id: client.client_id!,
      }),
    );
    expect(response.status).toBe(200);
  });

  it('rejects tokens issued before replay tracking was introduced', async () => {
    const { body: client } = await register();
    const sealer = createSealer(tokenSecret);
    const oldRefresh =
      'pmcp_rt_' +
      sealer.seal(
        'refresh',
        {
          clientId: client.client_id!,
          apiKey: VALID_API_KEY,
        },
        3600,
      );
    const refreshResponse = await fetch(
      `${baseUrl}/token`,
      form({
        grant_type: 'refresh_token',
        refresh_token: oldRefresh,
        client_id: client.client_id!,
      }),
    );
    expect(await refreshResponse.json()).toMatchObject({ error: 'invalid_grant' });

    const verifier = randomBytes(32).toString('base64url');
    const oldCode =
      'pmcp_code_' +
      sealer.seal(
        'code',
        {
          clientId: client.client_id!,
          apiKey: VALID_API_KEY,
          redirectUri: REDIRECT_URI,
          codeChallenge: s256(verifier),
          jti: 'old-code',
        },
        300,
      );
    const codeResponse = await fetch(
      `${baseUrl}/token`,
      form({
        grant_type: 'authorization_code',
        code: oldCode,
        code_verifier: verifier,
        client_id: client.client_id!,
      }),
    );
    expect(await codeResponse.json()).toMatchObject({ error: 'invalid_grant' });
  });

  it('rotates refresh tokens and rejects reuse', async () => {
    const { clientId, tokens } = await obtainTokens();
    const refresh = (token: string) =>
      fetch(`${baseUrl}/token`, form({ grant_type: 'refresh_token', refresh_token: token, client_id: clientId }));

    const response = await refresh(tokens.refresh_token!);
    expect(response.status).toBe(200);
    const rotated = (await response.json()) as Record<string, string>;
    expect(rotated.access_token).toMatch(/^pmcp_at_/);
    expect(rotated.refresh_token).not.toBe(tokens.refresh_token);
    expect((await refresh(tokens.refresh_token!)).status).toBe(400);
    expect((await refresh(`${tokens.refresh_token!}!`)).status).toBe(400);
    expect((await refresh(rotated.refresh_token!)).status).toBe(200);
  });

  it('accepts only one of two concurrent refresh requests and keeps the session', async () => {
    const { clientId, tokens } = await obtainTokens();
    const refresh = () =>
      fetch(
        `${baseUrl}/token`,
        form({
          grant_type: 'refresh_token',
          refresh_token: tokens.refresh_token!,
          client_id: clientId,
        }),
      );
    const responses = await Promise.all([refresh(), refresh()]);
    expect(responses.map((response) => response.status).sort()).toEqual([200, 400]);
    const winner = responses.find((response) => response.status === 200)!;
    const { refresh_token: rotated } = (await winner.json()) as Record<string, string>;
    const next = await fetch(
      `${baseUrl}/token`,
      form({ grant_type: 'refresh_token', refresh_token: rotated!, client_id: clientId }),
    );
    expect(next.status).toBe(200);
  });

  it('accepts the consent form posted by a browser with its real Origin', async () => {
    const { body: client } = await register();
    const page = await fetch(
      `${baseUrl}/authorize?${new URLSearchParams({
        response_type: 'code',
        client_id: client.client_id!,
        redirect_uri: REDIRECT_URI,
        code_challenge: s256('v'.repeat(43)),
        code_challenge_method: 'S256',
      })}`,
    );
    expect(await page.text()).toContain('<meta name="referrer" content="same-origin">');
    expect(page.headers.get('referrer-policy')).toBe('same-origin');

    const submit = (origin: string) =>
      fetch(`${baseUrl}/authorize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Origin: origin },
        body: new URLSearchParams({
          response_type: 'code',
          client_id: client.client_id!,
          redirect_uri: REDIRECT_URI,
          code_challenge: s256('v'.repeat(43)),
          code_challenge_method: 'S256',
          api_key: VALID_API_KEY,
        }),
        redirect: 'manual',
      });
    expect((await submit(baseUrl)).status).toBe(302);
    expect((await submit('https://evil.example')).status).toBe(403);
  });

  it('accepts offline_access next to the connector scope', async () => {
    const { body: client } = await register();
    const response = await fetch(`${baseUrl}/authorize`, {
      ...form({
        response_type: 'code',
        client_id: client.client_id!,
        redirect_uri: REDIRECT_URI,
        code_challenge: s256('v'.repeat(43)),
        code_challenge_method: 'S256',
        scope: 'pneumatic offline_access',
        api_key: VALID_API_KEY,
      }),
      redirect: 'manual',
    });
    expect(new URL(response.headers.get('location')!).searchParams.get('code')).toBeTruthy();
  });

  it('revokes the whole session when an old refresh token is replayed later', async () => {
    const { clientId, tokens } = await obtainTokens();
    const refresh = (token: string) =>
      fetch(`${baseUrl}/token`, form({ grant_type: 'refresh_token', refresh_token: token, client_id: clientId }));
    const rotated = (await (await refresh(tokens.refresh_token!)).json()) as Record<string, string>;

    const realNow = Date.now;
    vi.spyOn(Date, 'now').mockImplementation(() => realNow() + 60_000);
    try {
      expect((await refresh(tokens.refresh_token!)).status).toBe(400);
      expect((await refresh(rotated.refresh_token!)).status).toBe(400);
      const mcp = await fetch(`${baseUrl}/mcp`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${rotated.access_token}`, 'Content-Type': 'application/json' },
        body: '{}',
      });
      expect(mcp.status).toBe(401);
    } finally {
      vi.restoreAllMocks();
    }
  });

  it('keeps refresh races and late replays correct with a slow shared replay store', async () => {
    const slowServer = createServer();
    const ledger = join(replayDirectory, 'slow.json');
    writeFileSync(ledger, '');
    try {
      await new Promise<void>((resolve) => slowServer.listen(0, '127.0.0.1', resolve));
      const { port } = slowServer.address() as AddressInfo;
      const url = `http://127.0.0.1:${port}`;
      slowServer.on(
        'request',
        createHttpApp(
          {
            transport: 'http',
            pneumatic: { apiUrl: fake.apiUrl },
            host: '127.0.0.1',
            port,
            publicUrl: new URL(url),
            tokenSecret,
            replayFile: ledger,
            allowedRedirectHosts: ['claude.ai'],
            rateLimitPerMinute: 0,
            trustProxy: false,
          },
          fake.fetchFn,
          { replay: delayed(createFileReplayStore(ledger)) },
        ),
      );
      const { body: client } = await register({}, url);
      const verifier = randomBytes(32).toString('base64url');
      const code = new URL(
        (await authorize(client.client_id!, verifier, VALID_API_KEY, url)).headers.get('location')!,
      ).searchParams.get('code')!;
      const tokenRequest = (values: Record<string, string>) =>
        fetch(`${url}/token`, form({ client_id: client.client_id!, ...values }));
      const tokens = (await (
        await tokenRequest({
          grant_type: 'authorization_code',
          code,
          code_verifier: verifier,
          redirect_uri: REDIRECT_URI,
        })
      ).json()) as Record<string, string>;
      const refresh = (token: string) => tokenRequest({ grant_type: 'refresh_token', refresh_token: token });

      const raced = await Promise.all([refresh(tokens.refresh_token!), refresh(tokens.refresh_token!)]);
      const winner = (await raced.find((response) => response.status === 200)!.json()) as Record<string, string>;
      const next = (await (await refresh(winner.refresh_token!)).json()) as Record<string, string>;
      expect(next.refresh_token).toMatch(/^pmcp_rt_/);

      const realNow = Date.now;
      vi.spyOn(Date, 'now').mockImplementation(() => realNow() + 60_000);
      try {
        expect((await refresh(winner.refresh_token!)).status).toBe(400);
        expect((await refresh(next.refresh_token!)).status).toBe(400);
      } finally {
        vi.restoreAllMocks();
      }
    } finally {
      await new Promise<void>((resolve) => slowServer.close(() => resolve()));
    }
  });

  it('requires the registered client authentication method', async () => {
    for (const method of ['client_secret_basic', 'client_secret_post'] as const) {
      const { body: client } = await register({ token_endpoint_auth_method: method });
      const verifier = randomBytes(32).toString('base64url');
      const redirect = new URL((await authorize(client.client_id!, verifier)).headers.get('location')!);
      const values = {
        grant_type: 'authorization_code',
        code: redirect.searchParams.get('code')!,
        code_verifier: verifier,
        client_id: client.client_id!,
        redirect_uri: REDIRECT_URI,
      };
      const postAuth = form({ ...values, client_secret: client.client_secret! });
      const basicAuth = {
        ...form(values),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Authorization: `Basic ${Buffer.from(`${client.client_id}:${client.client_secret}`).toString('base64')}`,
        },
      };
      const wrong = method === 'client_secret_basic' ? postAuth : basicAuth;
      const correct = method === 'client_secret_basic' ? basicAuth : postAuth;
      expect((await fetch(`${baseUrl}/token`, wrong)).status).toBe(401);
      expect((await fetch(`${baseUrl}/token`, correct)).status).toBe(200);
    }
  });

  it('requires legacy confidential clients to register again', async () => {
    const sealer = createSealer(tokenSecret);
    const clientId =
      'pmcp_c_' +
      sealer.seal('client', {
        name: 'old client',
        redirectUris: [REDIRECT_URI],
        confidential: true,
      });
    const response = await fetch(
      `${baseUrl}/token`,
      form({
        grant_type: 'refresh_token',
        refresh_token: 'pmcp_rt_x',
        client_id: clientId,
        client_secret: sealer.sign(clientId),
      }),
    );
    expect(response.status).toBe(401);
    expect(await response.json()).toMatchObject({ error: 'invalid_client' });
  });

  it('requires the client secret for confidential clients', async () => {
    const { body: client } = await register({ token_endpoint_auth_method: 'client_secret_post' });
    expect(client.client_secret).toBeTruthy();
    const response = await fetch(
      `${baseUrl}/token`,
      form({ grant_type: 'refresh_token', refresh_token: 'pmcp_rt_x', client_id: client.client_id! }),
    );
    expect(response.status).toBe(401);
  });

  it('rejects malformed Basic authentication even when the form contains a valid secret', async () => {
    const { body: client } = await register({ token_endpoint_auth_method: 'client_secret_post' });
    const response = await fetch(`${baseUrl}/token`, {
      ...form({ grant_type: 'refresh_token', client_id: client.client_id!, client_secret: client.client_secret! }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Authorization: `Basic ${Buffer.from('missing-colon').toString('base64')}`,
      },
    });
    expect(response.status).toBe(401);
  });
});

describe('health', () => {
  it('reports an unusable replay ledger after an append failure', async () => {
    const directory = mkdtempSync(join(tmpdir(), 'pneumatic-health-'));
    const path = join(directory, 'used.log');
    writeFileSync(path, '');
    const isolatedServer = createServer();
    try {
      await new Promise<void>((resolve) => isolatedServer.listen(0, '127.0.0.1', resolve));
      const url = `http://127.0.0.1:${(isolatedServer.address() as AddressInfo).port}`;
      const config: HttpConfig = {
        transport: 'http',
        pneumatic: { apiUrl: fake.apiUrl },
        host: '127.0.0.1',
        port: (isolatedServer.address() as AddressInfo).port,
        publicUrl: new URL(url),
        tokenSecret,
        replayFile: path,
        allowedRedirectHosts: ['claude.ai'],
        rateLimitPerMinute: 0,
        trustProxy: false,
      };
      const app = createHttpApp(config, fake.fetchFn);
      const handleError: ErrorRequestHandler = (_error, _req, res, _next) => {
        res.status(500).end();
      };
      app.use(handleError);
      isolatedServer.on('request', app);
      expect((await fetch(`${url}/healthz`)).status).toBe(200);

      const { body: client } = await register({}, url);
      const verifier = randomBytes(32).toString('base64url');
      const redirect = new URL(
        (await authorize(client.client_id!, verifier, VALID_API_KEY, url)).headers.get('location')!,
      );
      renameSync(path, `${path}.saved`);
      mkdirSync(path);
      const response = await fetch(
        `${url}/token`,
        form({
          grant_type: 'authorization_code',
          client_id: client.client_id!,
          code: redirect.searchParams.get('code')!,
          code_verifier: verifier,
          redirect_uri: REDIRECT_URI,
        }),
      );
      expect(response.status).toBe(500);
      expect((await fetch(`${url}/healthz`)).status).toBe(503);
    } finally {
      if (isolatedServer.listening) {
        await new Promise<void>((resolve) => isolatedServer.close(() => resolve()));
      }
      rmSync(directory, { recursive: true, force: true });
    }
  });
});

describe('MCP endpoint', () => {
  it('serves tools with an OAuth access token using the stored API key', async () => {
    const { tokens } = await obtainTokens();
    const client = await connect(tokens.access_token!);
    const { tools } = await client.listTools();
    expect(tools.length).toBeGreaterThan(20);

    const result = await client.callTool({ name: 'get_current_user', arguments: {} });
    expect(JSON.parse((result.content as Array<{ text: string }>)[0]!.text)).toMatchObject({ data: { id: 7 } });
    expect(fake.lastRequest('/accounts/user')?.authorization).toBe(`Bearer ${VALID_API_KEY}`);
    await client.close();
  });

  it('accepts a raw Pneumatic API key as bearer token', async () => {
    const client = await connect(VALID_API_KEY);
    const result = await client.callTool({ name: 'list_templates', arguments: {} });
    expect(result.isError).toBeFalsy();
    await client.close();
  });

  it('limits MCP requests per key, failed consents per IP and sets security headers', async () => {
    const limitedServer = createServer();
    try {
      await new Promise<void>((resolve) => limitedServer.listen(0, '127.0.0.1', resolve));
      const { port } = limitedServer.address() as AddressInfo;
      const url = `http://127.0.0.1:${port}`;
      limitedServer.on(
        'request',
        createHttpApp(
          {
            transport: 'http',
            pneumatic: { apiUrl: fake.apiUrl },
            host: '127.0.0.1',
            port,
            publicUrl: new URL(url),
            tokenSecret,
            replayFile: join(replayDirectory, 'used.json'),
            allowedRedirectHosts: ['claude.ai'],
            rateLimitPerMinute: 2,
            trustProxy: false,
          },
          fake.fetchFn,
        ),
      );
      const post = () =>
        fetch(`${url}/mcp`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${VALID_API_KEY}`,
            'Content-Type': 'application/json',
            Accept: 'application/json, text/event-stream',
          },
          body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'ping' }),
        });
      expect((await post()).status).not.toBe(429);
      expect((await post()).status).not.toBe(429);
      const limited = await post();
      expect(limited.status).toBe(429);
      expect(limited.headers.get('retry-after')).toBe('60');
      const health = await fetch(`${url}/healthz`);
      expect(health.headers.get('cache-control')).toBe('no-store');
      expect(health.headers.get('referrer-policy')).toBe('same-origin');

      const { body: client } = await register({}, url);
      for (let attempt = 0; attempt < 10; attempt += 1) {
        expect((await authorize(client.client_id!, 'v'.repeat(43), 'pn-guess', url)).status).toBe(400);
      }
      expect((await authorize(client.client_id!, 'v'.repeat(43), 'pn-guess', url)).status).toBe(429);
    } finally {
      await new Promise<void>((resolve) => limitedServer.close(() => resolve()));
    }
  });

  it('accepts MCP bodies above the default JSON limit after authentication', async () => {
    const client = await connect(VALID_API_KEY);
    const result = await client.callTool({
      name: 'upload_file',
      arguments: { filename: 'big.txt', contentText: 'a'.repeat(300 * 1024) },
    });
    expect(result.isError).toBeFalsy();
    expect((result.structuredContent as { data: { size: number } }).data.size).toBe(300 * 1024);
    await client.close();

    const unauthenticated = await fetch(`${baseUrl}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ padding: 'a'.repeat(300 * 1024) }),
    });
    expect(unauthenticated.status).toBe(413);
  });

  it('rejects revoked keys and forged tokens', async () => {
    for (const token of ['pn-revoked', 'pmcp_at_forged']) {
      const response = await fetch(`${baseUrl}/mcp`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: '{}',
      });
      expect(response.status).toBe(401);
    }
  });
});

describe('browser uploads', () => {
  async function createLink(filename = 'contract.pdf') {
    const client = await connect(VALID_API_KEY);
    const result = await client.callTool({ name: 'create_upload_link', arguments: { filename } });
    return { client, link: (result.structuredContent as { data: { uploadId: string; uploadUrl: string } }).data };
  }

  function postFile(uploadUrl: string, content: string, origin = baseUrl) {
    const body = new FormData();
    body.append('file', new Blob([content], { type: 'application/pdf' }), 'contract.pdf');
    return fetch(uploadUrl, { method: 'POST', headers: { Origin: origin }, body });
  }

  it('stores a file picked on the upload page and reports it to the model once', async () => {
    const { client, link } = await createLink();
    expect(link.uploadUrl.startsWith(`${baseUrl}/upload/`)).toBe(true);

    const page = await fetch(link.uploadUrl);
    expect(page.status).toBe(200);
    expect(page.headers.get('content-security-policy')).toContain("form-action 'self'");
    expect(await page.text()).toContain('contract.pdf');

    const pending = await client.callTool({ name: 'get_upload_status', arguments: { uploadId: link.uploadId } });
    expect((pending.structuredContent as { data: { status: string } }).data.status).toBe('pending');

    const uploaded = await postFile(link.uploadUrl, '%PDF-1.7');
    expect(uploaded.status).toBe(200);
    expect(await uploaded.text()).toContain('File uploaded');

    const ready = await client.callTool({ name: 'get_upload_status', arguments: { uploadId: link.uploadId } });
    const { data } = ready.structuredContent as {
      data: { status: string; file: { fileId: string; size: number; fieldValue: string } };
    };
    expect(data.status).toBe('ready');
    expect(data.file).toMatchObject({ size: 8, fieldValue: expect.stringMatching(/^\[contract\.pdf\]\(.+\)$/) });
    expect(fake.files.get(data.file.fileId)?.data.toString()).toBe('%PDF-1.7');

    expect((await postFile(link.uploadUrl, 'again')).status).toBe(404);
    expect((await fetch(link.uploadUrl)).status).toBe(404);
    await client.close();
  });

  it('keeps the link usable when storage fails and rejects oversized files', async () => {
    const { client, link } = await createLink();
    fake.state.storageDown = true;
    const failed = await postFile(link.uploadUrl, 'x');
    expect(failed.status).toBe(502);
    fake.state.storageDown = false;
    expect((await postFile(link.uploadUrl, 'x'.repeat(26 * 1024 * 1024))).status).toBe(413);
    expect((await postFile(link.uploadUrl, 'ok')).status).toBe(200);
    await client.close();
  });

  it('rejects forged links, foreign origins and unknown upload IDs', async () => {
    const { client, link } = await createLink();
    expect((await fetch(`${baseUrl}/upload/forged-token`)).status).toBe(404);
    expect((await postFile(link.uploadUrl, 'x', 'https://evil.example')).status).toBe(403);
    const unknown = await client.callTool({
      name: 'get_upload_status',
      arguments: { uploadId: '00000000-0000-4000-8000-000000000000' },
    });
    expect((unknown.structuredContent as { error: { code: string } }).error.code).toBe('not_found');
    await client.close();
  });

  it('stores one file when two posts race on a link backed by an injected store', async () => {
    const racingServer = createServer();
    try {
      await new Promise<void>((resolve) => racingServer.listen(0, '127.0.0.1', resolve));
      const { port } = racingServer.address() as AddressInfo;
      const url = `http://127.0.0.1:${port}`;
      racingServer.on(
        'request',
        createHttpApp(
          {
            transport: 'http',
            pneumatic: { apiUrl: fake.apiUrl, filesUrl: fake.filesUrl },
            host: '127.0.0.1',
            port,
            publicUrl: new URL(url),
            tokenSecret,
            replayFile: join(replayDirectory, 'used.json'),
            allowedRedirectHosts: ['claude.ai'],
            rateLimitPerMinute: 0,
            trustProxy: false,
          },
          fake.fetchFn,
          { uploads: delayed(createMemoryUploadStore()) },
        ),
      );
      const client = new Client({ name: 'test', version: '1.0.0' });
      await client.connect(
        new StreamableHTTPClientTransport(new URL(`${url}/mcp`), {
          requestInit: { headers: { Authorization: `Bearer ${VALID_API_KEY}` } },
        }),
      );
      const created = await client.callTool({ name: 'create_upload_link', arguments: {} });
      const { uploadUrl } = (created.structuredContent as { data: { uploadUrl: string } }).data;
      const filesBefore = fake.files.size;
      const post = (content: string) => {
        const body = new FormData();
        body.append('file', new Blob([content]), 'race.txt');
        return fetch(uploadUrl, { method: 'POST', headers: { Origin: url }, body });
      };
      const statuses = (await Promise.all([post('first'), post('second')])).map((response) => response.status);
      expect(statuses.filter((status) => status === 200)).toHaveLength(1);
      expect(fake.files.size - filesBefore).toBe(1);
      await client.close();
    } finally {
      await new Promise<void>((resolve) => racingServer.close(() => resolve()));
    }
  });

  it('limits open upload links per API key', async () => {
    const client = await connect(VALID_API_KEY);
    let error: { code: string } | undefined;
    for (let index = 0; index < 25 && !error; index += 1) {
      const result = await client.callTool({ name: 'create_upload_link', arguments: {} });
      error = (result.structuredContent as { error?: { code: string } }).error;
    }
    expect(error?.code).toBe('rate_limited');
    await client.close();
  });
});

import { randomBytes } from 'node:crypto';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, request, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { Client, InMemoryTransport } from '@modelcontextprotocol/client';
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import packageJson from '../package.json' with { type: 'json' };

import { configureLog } from '../src/core/log.js';
import { renderMetrics, resetMetrics } from '../src/core/metrics.js';
import { VERSION } from '../src/core/version.js';
import { createHttpApp } from '../src/http/app.js';
import { createPneumaticClient } from '../src/pneumatic/client.js';
import { buildServer } from '../src/server.js';
import { createFakePneumatic, VALID_API_KEY } from './fakePneumatic.js';

const METRICS_TOKEN = 'metrics-token-123456';
const fake = createFakePneumatic();
const lines: Array<Record<string, unknown>> = [];
const directory = mkdtempSync(join(tmpdir(), 'pneumatic-observability-'));
let server: Server;
let baseUrl: string;

beforeAll(async () => {
  configureLog('info', (line) => lines.push(JSON.parse(line) as Record<string, unknown>));
  server = createServer();
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address() as AddressInfo;
  baseUrl = `http://127.0.0.1:${port}`;
  const replayFile = join(directory, 'replay.json');
  writeFileSync(replayFile, '');
  server.on(
    'request',
    createHttpApp(
      {
        transport: 'http',
        pneumatic: { apiUrl: fake.apiUrl, filesUrl: fake.filesUrl },
        host: '127.0.0.1',
        port,
        publicUrl: new URL(baseUrl),
        tokenSecret: randomBytes(32).toString('hex'),
        replayFile,
        allowedRedirectHosts: ['claude.ai'],
        rateLimitPerMinute: 0,
        trustProxy: false,
        metricsToken: METRICS_TOKEN,
      },
      fake.fetchFn,
    ),
  );
});

afterEach(() => {
  lines.length = 0;
});

afterAll(async () => {
  configureLog('off');
  resetMetrics();
  await new Promise((resolve) => server.close(resolve));
  rmSync(directory, { recursive: true, force: true });
});

describe('tool call telemetry', () => {
  it('logs and counts tool calls without arguments or credentials', async () => {
    const mcpServer = buildServer(createPneumaticClient({ apiUrl: fake.apiUrl }, VALID_API_KEY, fake.fetchFn));
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    const client = new Client({ name: 'test', version: '1.0.0' });
    await mcpServer.connect(serverTransport);
    await client.connect(clientTransport);
    await client.callTool({ name: 'comment_on_task', arguments: { taskId: 3, text: 'secret note' } });
    await client.close();

    const call = lines.find((line) => line.event === 'tool_call');
    expect(call).toMatchObject({ level: 'info', tool: 'comment_on_task', outcome: 'ok' });
    expect(JSON.stringify(lines)).not.toContain('secret note');
    expect(JSON.stringify(lines)).not.toContain(VALID_API_KEY);
    expect(renderMetrics()).toContain('mcp_tool_calls_total{outcome="ok",tool="comment_on_task"} 1');
    expect(renderMetrics()).toContain('pneumatic_requests_total{method="POST",status="2xx",target="api"}');
  });
});

describe('HTTP telemetry', () => {
  it('protects /metrics with a bearer token', async () => {
    expect((await fetch(`${baseUrl}/metrics`)).status).toBe(401);
    const response = await fetch(`${baseUrl}/metrics`, { headers: { Authorization: `Bearer ${METRICS_TOKEN}` } });
    expect(response.status).toBe(200);
    expect(await response.text()).toContain('http_requests_total{route="metrics",status="401"}');
  });

  it('logs requests with a request ID and never logs upload tokens', async () => {
    const response = await fetch(`${baseUrl}/upload/very-secret-capability`, { headers: { 'X-Request-Id': 'req-42' } });
    expect(response.headers.get('x-request-id')).toBe('req-42');
    const entry = lines.find((line) => line.event === 'http_request' && line.requestId === 'req-42');
    expect(entry).toMatchObject({ route: 'upload', status: 404, method: 'GET' });
    expect(JSON.stringify(lines)).not.toContain('very-secret-capability');
  });
});

describe('request errors', () => {
  it('answers malformed bodies without printing them', async () => {
    const printed = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    try {
      const response = await fetch(`${baseUrl}/anything`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{"apiKey":"pn-SECRETSECRET", bad',
      });
      expect(response.status).toBe(400);
      expect(await response.text()).not.toContain('SECRET');
      expect(printed).not.toHaveBeenCalled();
      expect(lines.find((line) => line.event === 'http_error')).toMatchObject({
        route: 'other',
        status: 400,
        type: 'entity.parse.failed',
      });
      expect(JSON.stringify(lines)).not.toContain('SECRET');
    } finally {
      printed.mockRestore();
    }
  });

  it('serves /metrics to scrapers that use a service name as Host', async () => {
    const { port } = server.address() as AddressInfo;
    const status = await new Promise<number | undefined>((resolve, reject) => {
      request(
        {
          host: '127.0.0.1',
          port,
          path: '/metrics',
          headers: { Host: 'connector:3917', Authorization: `Bearer ${METRICS_TOKEN}` },
        },
        (response) => {
          response.resume();
          resolve(response.statusCode);
        },
      )
        .on('error', reject)
        .end();
    });
    expect(status).toBe(200);
  });
});

describe('configuration', () => {
  it('rejects unknown log levels', () => {
    expect(() => configureLog('verbose')).toThrow('LOG_LEVEL');
    expect(() => configureLog('constructor')).toThrow('LOG_LEVEL');
  });

  it('keeps the server version equal to package.json', () => {
    expect(VERSION).toBe(packageJson.version);
  });
});

import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { ConfigError, loadConfig } from '../src/config.js';

const replayFile = join(mkdtempSync(join(tmpdir(), 'pneumatic-config-')), 'replay.json');
writeFileSync(replayFile, '');

const httpEnv = {
  MCP_TRANSPORT: 'http',
  TOKEN_SECRET: 'a'.repeat(32),
  OAUTH_REPLAY_FILE: replayFile,
};

describe('HTTP configuration', () => {
  it('accepts a secure public origin and local HTTP', () => {
    expect(loadConfig([], { ...httpEnv, PUBLIC_URL: 'https://mcp.example.com' })).toMatchObject({
      publicUrl: new URL('https://mcp.example.com'),
    });
    expect(loadConfig([], httpEnv)).toMatchObject({ publicUrl: new URL('http://localhost:3000') });
  });

  it.each([
    { PUBLIC_URL: 'not a URL' },
    { PUBLIC_URL: 'http://mcp.example.com' },
    { PUBLIC_URL: 'https://mcp.example.com/subpath' },
    { PUBLIC_URL: 'https://user:mypassword@mcp.example.com' },
    { PORT: '65536' },
    { RATE_LIMIT_PER_MINUTE: '-1' },
    { OAUTH_REPLAY_FILE: join(tmpdir(), 'missing-pneumatic-replay.json') },
    { PNEUMATIC_API_URL: 'ftp://pneumatic.example.com' },
    { PNEUMATIC_API_URL: 'not a url' },
    { PNEUMATIC_FILES_URL: 'ftp://files.example.com' },
    { PNEUMATIC_FILES_URL: 'https://files.example.com/files?x=1' },
  ])('rejects an invalid origin or port: %j', (override) => {
    expect(() => loadConfig([], { ...httpEnv, ...override })).toThrow(ConfigError);
  });
});

describe('file storage configuration', () => {
  const stdioEnv = { PNEUMATIC_API_KEY: 'pn-key' };

  it('defaults to Pneumatic Cloud storage only for the Cloud API', () => {
    expect(loadConfig([], stdioEnv)).toMatchObject({ pneumatic: { filesUrl: 'https://my.pneumatic.app/files' } });
    expect(
      loadConfig([], { ...stdioEnv, PNEUMATIC_API_URL: 'https://pneumatic.internal' }).pneumatic.filesUrl,
    ).toBeUndefined();
  });

  it('normalizes an explicit storage URL', () => {
    expect(
      loadConfig([], {
        ...stdioEnv,
        PNEUMATIC_API_URL: 'https://pneumatic.internal',
        PNEUMATIC_FILES_URL: 'https://app.internal/files/',
      }),
    ).toMatchObject({ pneumatic: { filesUrl: 'https://app.internal/files' } });
  });

  it('reads an internal storage URL only alongside the public one', () => {
    expect(
      loadConfig([], {
        ...stdioEnv,
        PNEUMATIC_FILES_URL: 'http://localhost/files',
        PNEUMATIC_FILES_INTERNAL_URL: 'http://pneumatic-file-service:8000/',
      }),
    ).toMatchObject({
      pneumatic: { filesUrl: 'http://localhost/files', filesInternalUrl: 'http://pneumatic-file-service:8000' },
    });
    expect(loadConfig([], stdioEnv).pneumatic.filesInternalUrl).toBeUndefined();
    expect(() =>
      loadConfig([], {
        ...stdioEnv,
        PNEUMATIC_API_URL: 'https://pneumatic.internal',
        PNEUMATIC_FILES_INTERNAL_URL: 'http://pneumatic-file-service:8000',
      }),
    ).toThrow(ConfigError);
  });
});

describe('proxy trust', () => {
  it('trusts loopback and private-network proxies by default and accepts booleans and hop counts', () => {
    expect(loadConfig([], httpEnv)).toMatchObject({ trustProxy: 'loopback,uniquelocal' });
    expect(loadConfig([], { ...httpEnv, TRUST_PROXY: 'false' })).toMatchObject({ trustProxy: false });
    expect(loadConfig([], { ...httpEnv, TRUST_PROXY: '2' })).toMatchObject({ trustProxy: 2 });
  });
});

describe('web app links', () => {
  it('derives the app URL from the storage URL unless set explicitly', () => {
    expect(loadConfig([], { PNEUMATIC_API_KEY: 'pn-key' })).toMatchObject({
      pneumatic: { appUrl: 'https://my.pneumatic.app' },
    });
    expect(
      loadConfig([], {
        PNEUMATIC_API_KEY: 'pn-key',
        PNEUMATIC_API_URL: 'https://api.internal',
        PNEUMATIC_APP_URL: 'https://app.internal/',
      }),
    ).toMatchObject({ pneumatic: { appUrl: 'https://app.internal' } });
    expect(
      loadConfig([], { PNEUMATIC_API_KEY: 'pn-key', PNEUMATIC_API_URL: 'https://api.internal' }).pneumatic.appUrl,
    ).toBeUndefined();
    expect(
      loadConfig([], {
        PNEUMATIC_API_KEY: 'pn-key',
        PNEUMATIC_API_URL: 'https://api.internal',
        PNEUMATIC_FILES_URL: 'https://files.internal',
      }).pneumatic.appUrl,
    ).toBeUndefined();
  });
});

describe('tool catalog options', () => {
  it('parses toolsets and read-only mode for both transports', () => {
    expect(loadConfig([], { PNEUMATIC_API_KEY: 'pn-key' })).toMatchObject({ toolsets: undefined, isReadOnly: false });
    expect(loadConfig([], { PNEUMATIC_API_KEY: 'pn-key', TOOLSETS: 'core, Files', READ_ONLY: 'yes' })).toMatchObject({
      toolsets: ['core', 'files'],
      isReadOnly: true,
    });
    expect(loadConfig([], { ...httpEnv, TOOLSETS: 'all' })).toMatchObject({ toolsets: undefined });
    expect(() => loadConfig([], { PNEUMATIC_API_KEY: 'pn-key', TOOLSETS: 'core,billing' })).toThrow(ConfigError);
    expect(() => loadConfig([], { PNEUMATIC_API_KEY: 'pn-key', READ_ONLY: 'maybe' })).toThrow(ConfigError);
    expect(() => loadConfig([], { ...httpEnv, METRICS_TOKEN: 'short' })).toThrow(ConfigError);
  });
});

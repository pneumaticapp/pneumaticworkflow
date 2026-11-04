import { existsSync } from 'node:fs';

import { isLoopbackHost, LOOPBACK_HOSTS } from './core/net.js';
import { TOOLSETS, type Toolset, type ToolSelection } from './mcp/toolDef.js';

export type Transport = 'stdio' | 'http';

export interface StdioConfig extends ToolSelection {
  transport: 'stdio';
  apiUrl: string;
  filesUrl?: string;
  appUrl?: string;
  apiKey: string;
}

export interface HttpConfig extends ToolSelection {
  transport: 'http';
  apiUrl: string;
  filesUrl?: string;
  appUrl?: string;
  host: string;
  port: number;
  publicUrl: URL;
  tokenSecret: string;
  replayFile: string;
  allowedRedirectHosts: string[];
  rateLimitPerMinute: number;
  trustProxy: boolean | number | string;
  metricsToken?: string;
}

export type Config = StdioConfig | HttpConfig;

const DEFAULT_API_URL = 'https://api.pneumatic.app';

const DEFAULT_FILES_URL = 'https://my.pneumatic.app/files';

const DEFAULT_RATE_LIMIT_PER_MINUTE = 120;

const DEFAULT_REDIRECT_HOSTS = ['claude.ai', 'claude.com', ...LOOPBACK_HOSTS];

export class ConfigError extends Error {}

function readTransport(argv: string[], env: NodeJS.ProcessEnv): Transport {
  if (argv.includes('--http')) {
    return 'http';
  }
  if (argv.includes('--stdio')) {
    return 'stdio';
  }
  const value = env.MCP_TRANSPORT ?? 'stdio';
  if (value !== 'stdio' && value !== 'http') {
    throw new ConfigError(`MCP_TRANSPORT must be "stdio" or "http", got "${value}"`);
  }
  return value;
}

function readList(value: string | undefined): string[] | undefined {
  if (!value) {
    return undefined;
  }
  return value
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function parseBaseUrl(name: string, value: string): URL {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new ConfigError(`${name} must be a valid URL`);
  }
  if (!['http:', 'https:'].includes(url.protocol) || url.search || url.hash || url.username || url.password) {
    throw new ConfigError(`${name} must be an HTTP(S) URL without query, fragment or credentials`);
  }
  return url;
}

// Returned as given rather than as url.href: the client identity hashes it and the files URL default compares it.
function readApiUrl(env: NodeJS.ProcessEnv): string {
  const value = (env.PNEUMATIC_API_URL ?? DEFAULT_API_URL).trim();
  parseBaseUrl('PNEUMATIC_API_URL', value);
  return value.replace(/\/+$/, '');
}

// Express "trust proxy": true/false, a hop count, or comma-separated subnets. The default also trusts private
// networks because a Docker container sees the host's reverse proxy through the bridge gateway (e.g. 172.17.0.1).
function readTrustProxy(value: string | undefined): boolean | number | string {
  const trimmed = value?.trim() || 'loopback,uniquelocal';
  if (trimmed === 'true' || trimmed === 'false') {
    return trimmed === 'true';
  }
  return /^\d+$/.test(trimmed) ? Number(trimmed) : trimmed;
}

// Links in results point to the Pneumatic web app; its storage URL is usually <app>/files.
function readAppUrl(env: NodeJS.ProcessEnv, filesUrl: string | undefined): string | undefined {
  const derived = filesUrl?.endsWith('/files') ? filesUrl.slice(0, -'/files'.length) : undefined;
  const value = env.PNEUMATIC_APP_URL?.trim() || derived;
  if (!value) {
    return undefined;
  }
  return parseBaseUrl('PNEUMATIC_APP_URL', value).href.replace(/\/+$/, '');
}

function readToolOptions(env: NodeJS.ProcessEnv): ToolSelection {
  const listed = readList(env.TOOLSETS);
  const unknown = (listed ?? []).filter((item) => item !== 'all' && !(TOOLSETS as readonly string[]).includes(item));
  if (unknown.length) {
    throw new ConfigError(`TOOLSETS has unknown entries (${unknown.join(', ')}); use ${TOOLSETS.join(', ')} or all`);
  }
  const readOnly = (env.READ_ONLY ?? '').trim().toLowerCase();
  if (readOnly && !['true', 'false', 'yes', 'no', '1', '0'].includes(readOnly)) {
    throw new ConfigError('READ_ONLY must be true or false');
  }
  return {
    toolsets: !listed?.length || listed.includes('all') ? undefined : (listed as Toolset[]),
    readOnly: ['true', 'yes', '1'].includes(readOnly),
  };
}

function readMetricsToken(value: string | undefined): string | undefined {
  const token = value?.trim();
  if (token && token.length < 16) {
    throw new ConfigError('METRICS_TOKEN must be at least 16 characters (leave it unset to disable /metrics)');
  }
  return token || undefined;
}

function readFilesUrl(env: NodeJS.ProcessEnv, apiUrl: string): string | undefined {
  const value = env.PNEUMATIC_FILES_URL?.trim() || (apiUrl === DEFAULT_API_URL ? DEFAULT_FILES_URL : undefined);
  if (!value) {
    return undefined;
  }
  return parseBaseUrl('PNEUMATIC_FILES_URL', value).href.replace(/\/+$/, '');
}

export function loadConfig(argv: string[] = process.argv.slice(2), env: NodeJS.ProcessEnv = process.env): Config {
  const transport = readTransport(argv, env);
  const apiUrl = readApiUrl(env);
  const filesUrl = readFilesUrl(env, apiUrl);
  const appUrl = readAppUrl(env, filesUrl);

  if (transport === 'stdio') {
    const apiKey = env.PNEUMATIC_API_KEY?.trim();
    if (!apiKey) {
      throw new ConfigError('PNEUMATIC_API_KEY is required in stdio mode');
    }
    return { transport, apiUrl, filesUrl, appUrl, apiKey, ...readToolOptions(env) };
  }

  const port = Number(env.PORT ?? 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new ConfigError(`PORT must be an integer from 1 to 65535, got "${env.PORT}"`);
  }
  const host = env.HOST ?? '127.0.0.1';
  let publicUrl: URL;
  try {
    publicUrl = new URL(env.PUBLIC_URL ?? `http://localhost:${port}`);
  } catch {
    throw new ConfigError('PUBLIC_URL must be a valid URL');
  }
  const isLoopback = isLoopbackHost(publicUrl.hostname);
  if (
    (publicUrl.protocol !== 'https:' && !(publicUrl.protocol === 'http:' && isLoopback)) ||
    publicUrl.pathname !== '/' ||
    publicUrl.search ||
    publicUrl.hash ||
    publicUrl.username ||
    publicUrl.password
  ) {
    throw new ConfigError('PUBLIC_URL must be an HTTPS origin (HTTP allowed only on loopback)');
  }

  const tokenSecret = env.TOKEN_SECRET ?? '';
  if (tokenSecret.length < 32) {
    throw new ConfigError('TOKEN_SECRET must be at least 32 characters in http mode (e.g. `openssl rand -hex 32`)');
  }

  const replayFile = env.OAUTH_REPLAY_FILE?.trim();
  if (replayFile && !existsSync(replayFile)) {
    throw new ConfigError(
      `OAUTH_REPLAY_FILE ${replayFile} does not exist; create it empty for a fresh install, never on upgrades`,
    );
  }
  if (!replayFile) {
    throw new ConfigError('OAUTH_REPLAY_FILE is required in http mode (use a persistent writable volume)');
  }

  const rateLimitPerMinute = Number(env.RATE_LIMIT_PER_MINUTE ?? DEFAULT_RATE_LIMIT_PER_MINUTE);
  if (!Number.isInteger(rateLimitPerMinute) || rateLimitPerMinute < 0) {
    throw new ConfigError('RATE_LIMIT_PER_MINUTE must be a non-negative integer (0 disables the limit)');
  }

  return {
    transport,
    apiUrl,
    filesUrl,
    appUrl,
    host,
    port,
    publicUrl,
    tokenSecret,
    replayFile,
    allowedRedirectHosts: readList(env.OAUTH_ALLOWED_REDIRECT_HOSTS) ?? DEFAULT_REDIRECT_HOSTS,
    rateLimitPerMinute,
    trustProxy: readTrustProxy(env.TRUST_PROXY),
    metricsToken: readMetricsToken(env.METRICS_TOKEN),
    ...readToolOptions(env),
  };
}

import {
  getOAuthProtectedResourceMetadataUrl,
  hostHeaderValidation,
  mcpAuthMetadataRouter,
  originValidation,
  requireBearerAuth,
} from '@modelcontextprotocol/express';
import { toNodeHandler } from '@modelcontextprotocol/node';
import { createMcpHandler } from '@modelcontextprotocol/server';
import { createHash, randomUUID, timingSafeEqual } from 'node:crypto';

import express, { type ErrorRequestHandler, type Express, type RequestHandler, type Response } from 'express';

import type { HttpConfig } from '../config.js';
import { hashApiKey } from '../core/keys.js';
import { log } from '../core/log.js';
import { count, renderMetrics } from '../core/metrics.js';
import { LOOPBACK_HOSTS } from '../core/net.js';
import type { RateLimiter, RateLimiterFactory, ReplayStore, UploadStore } from '../core/ports.js';
import { createClientFactory } from '../pneumatic/client.js';
import { buildServer } from '../server.js';
import { createFileReplayStore } from '../stores/fileReplayStore.js';
import { memoryRateLimiterFactory } from '../stores/memoryRateLimiter.js';
import { createMemoryUploadStore } from '../stores/memoryUploadStore.js';
import { createApiKeyValidator } from './apiKeyValidator.js';
import { buildOAuthMetadata, createOAuthRouter } from './oauth.js';
import { createTokenVerifier, SUPPORTED_SCOPES } from './oauthTokens.js';
import { createSealer } from './sealer.js';
import { mountUploadRoutes, uploadLinksFor } from './uploads.js';

// Inline upload_file content (up to 5 MiB, base64 or JSON-escaped text) must fit into one MCP request.
const MCP_BODY_LIMIT = '16mb';

const CONSENT_FAILURES_PER_MINUTE = 10;
const OAUTH_PATHS = new Set(['/register', '/token', '/authorize']);

function normalizePath(path: string): string {
  return path.toLowerCase().replace(/\/+$/, '');
}

function isMcpPath(path: string): boolean {
  return /^\/mcp\/?$/i.test(path);
}

// Route labels never contain path parameters: upload links carry their capability token in the path.
function routeOf(path: string): string {
  const lower = normalizePath(path);
  if (lower.startsWith('/upload/')) {
    return 'upload';
  }
  if (lower.startsWith('/.well-known/')) {
    return 'metadata';
  }
  return ['/mcp', '/token', '/authorize', '/register', '/healthz', '/metrics'].includes(lower)
    ? lower.slice(1)
    : 'other';
}

function sendJsonRpcError(res: Response, status: number, code: number, message: string, retryAfter?: string) {
  if (retryAfter) {
    res.set('Retry-After', retryAfter);
  }
  res.status(status).json({ jsonrpc: '2.0', error: { code, message }, id: null });
}

const requestLog: RequestHandler = (req, res, next) => {
  const started = performance.now();
  const given = req.headers['x-request-id'];
  const requestId = typeof given === 'string' && /^[\w.-]{1,64}$/.test(given) ? given : randomUUID();
  res.set('X-Request-Id', requestId);
  res.on('finish', () => {
    const route = routeOf(req.path);
    count('http_requests_total', 'HTTP requests by route and status', { route, status: String(res.statusCode) });
    const isProbe = (route === 'healthz' || route === 'metrics') && res.statusCode < 400;
    log(res.statusCode >= 500 ? 'error' : isProbe ? 'debug' : 'info', 'http_request', {
      requestId,
      method: req.method,
      route,
      status: res.statusCode,
      ms: Math.round(performance.now() - started),
    });
  });
  next();
};

function metricsRoute(token: string): RequestHandler {
  const digest = (value: string) => createHash('sha256').update(value).digest();
  const expected = digest(`Bearer ${token}`);
  return (req, res) => {
    res.set('Cache-Control', 'no-store');
    if (!timingSafeEqual(digest(req.headers.authorization ?? ''), expected)) {
      res.status(401).set('WWW-Authenticate', 'Bearer').end();
      return;
    }
    res.type('text/plain; version=0.0.4').send(renderMetrics());
  };
}

const securityHeaders: RequestHandler = (_req, res, next) => {
  // same-origin keeps form posts' Origin header intact while never leaking URLs to other sites.
  res.set({ 'Cache-Control': 'no-store', 'Referrer-Policy': 'same-origin', 'X-Content-Type-Options': 'nosniff' });
  next();
};

// Only rejected keys count, so key guessing through the consent form is throttled without blocking sign-ins.
function consentThrottle(consentFailures: RateLimiter): RequestHandler {
  return async (req, res, next) => {
    const ip = req.ip ?? 'unknown';
    // A failing limiter must not lock everyone out of signing in.
    if (await consentFailures.isExhausted(ip).catch(() => false)) {
      res.status(429).set('Retry-After', '60').type('text').send('Too many failed attempts. Try again in a minute.');
      return;
    }
    res.on('finish', () => {
      if (res.locals.keyRejected) {
        consentFailures.acquire(ip).catch(() => undefined);
      }
    });
    next();
  };
}

function mcpRateLimit(limiter: RateLimiter): RequestHandler {
  return async (req, res, next) => {
    const apiKey = String(req.auth?.extra?.apiKey ?? '');
    let isAllowed: boolean;
    try {
      isAllowed = await limiter.acquire(hashApiKey(apiKey));
    } catch {
      sendJsonRpcError(res, 503, -32000, 'The connector is temporarily unavailable.', '5');
      return;
    }
    if (isAllowed) {
      next();
      return;
    }
    sendJsonRpcError(res, 429, -32000, 'Rate limit exceeded. Try again later.', '60');
  };
}

// Ends every error chain: Express's default handler would print the error, including raw request bodies.
const handleErrors: ErrorRequestHandler = (error, req, res, _next) => {
  const { type, status: given } = error as { type?: string; status?: number };
  const status = typeof given === 'number' && given >= 400 && given < 600 ? given : 500;
  log(status >= 500 ? 'error' : 'warn', 'http_error', {
    requestId: String(res.getHeader('X-Request-Id') ?? ''),
    route: routeOf(req.path),
    status,
    type,
  });
  if (res.headersSent) {
    res.destroy();
    return;
  }
  if (isMcpPath(req.path)) {
    const [code, message] =
      type === 'entity.too.large'
        ? [-32600, 'Request body is too large.']
        : type === 'entity.parse.failed'
          ? [-32700, 'Parse error.']
          : [-32603, 'Internal error.'];
    sendJsonRpcError(res, status, code, message);
    return;
  }
  if (OAUTH_PATHS.has(normalizePath(req.path))) {
    if (type === 'entity.too.large' || type === 'entity.parse.failed') {
      res.status(type === 'entity.too.large' ? 413 : 400).json({
        error: 'invalid_request',
        error_description: 'The request body is malformed or too large',
      });
    } else {
      res.status(500).json({
        error: 'server_error',
        error_description: 'The authorization server could not complete the request',
      });
    }
    return;
  }
  res.status(status).end();
};

export interface HttpStores {
  replay: ReplayStore;
  uploads: UploadStore;
  rateLimiter: RateLimiterFactory;
}

export function createHttpApp(
  config: HttpConfig,
  fetchFn: typeof fetch = fetch,
  stores: Partial<HttpStores> = {},
): Express {
  const mcpUrl = new URL('/mcp', config.publicUrl);
  const sealer = createSealer(config.tokenSecret);
  const replayStore = stores.replay ?? createFileReplayStore(config.replayFile);
  const rateLimiter = stores.rateLimiter ?? memoryRateLimiterFactory;
  const clientFor = createClientFactory(config.pneumatic, fetchFn);
  const validator = createApiKeyValidator(clientFor);
  const mcpLimiter = rateLimiter('mcp-key', config.rateLimitPerMinute);
  const knownHosts = [...new Set([config.publicUrl.hostname, ...LOOPBACK_HOSTS])];

  const app = express();
  app.set('trust proxy', config.trustProxy);
  app.disable('x-powered-by');

  app.use(requestLog);
  // Mounted before Host validation so Prometheus can scrape by service name; the bearer token stops DNS rebinding.
  if (config.metricsToken) {
    app.get('/metrics', metricsRoute(config.metricsToken));
  }
  app.use(hostHeaderValidation(knownHosts));
  app.use(originValidation([...knownHosts, ...config.allowedRedirectHosts.filter((host) => host !== '*')]));
  // Large MCP bodies are parsed only after authentication; every other route keeps the default limit.
  const defaultJson = express.json();
  app.use((req, res, next) => (isMcpPath(req.path) ? next() : defaultJson(req, res, next)));
  app.use(securityHeaders);

  app.get('/healthz', async (_req, res) => {
    const isHealthy = await replayStore.isHealthy().catch(() => false);
    res.status(isHealthy ? 200 : 503).json({ status: isHealthy ? 'ok' : 'unhealthy' });
  });

  app.use(
    mcpAuthMetadataRouter({
      oauthMetadata: buildOAuthMetadata(config.publicUrl),
      resourceServerUrl: mcpUrl,
      resourceName: 'Pneumatic Workflow',
      scopesSupported: [...SUPPORTED_SCOPES],
    }),
  );
  app.post('/authorize', consentThrottle(rateLimiter('consent-ip', CONSENT_FAILURES_PER_MINUTE)));
  app.use(
    createOAuthRouter({
      issuer: config.publicUrl,
      sealer,
      validator,
      replayStore,
      allowedRedirectHosts: config.allowedRedirectHosts,
    }),
  );

  const uploads = config.pneumatic.filesUrl ? (stores.uploads ?? createMemoryUploadStore()) : undefined;
  if (uploads) {
    mountUploadRoutes(app, { store: uploads, sealer, clientFor });
  }

  const mcpHandler = toNodeHandler(
    createMcpHandler(({ authInfo }) => {
      const apiKey = authInfo?.extra?.apiKey;
      if (typeof apiKey !== 'string') {
        throw new Error('Missing Pneumatic credentials for the request');
      }
      return buildServer(clientFor(apiKey), {
        uploads: uploads && uploadLinksFor(uploads, sealer, config.publicUrl, apiKey),
        toolsets: config.toolsets,
        isReadOnly: config.isReadOnly,
      });
    }),
  );

  app.all(
    '/mcp',
    requireBearerAuth({
      verifier: createTokenVerifier(sealer, validator, replayStore),
      resourceMetadataUrl: getOAuthProtectedResourceMetadataUrl(mcpUrl),
    }),
    mcpRateLimit(mcpLimiter),
    express.json({ limit: MCP_BODY_LIMIT }),
    (req, res) => void mcpHandler(req, res, req.body),
  );

  app.use(handleErrors);

  return app;
}

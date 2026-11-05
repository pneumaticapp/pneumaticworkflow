import { randomBytes } from 'node:crypto';

import type { OAuthMetadata } from '@modelcontextprotocol/server';
import express, { type Request, type Response, Router } from 'express';

import { isLoopbackHost } from '../core/net.js';
import type { ReplayStore } from '../core/ports.js';
import { nowSeconds } from '../core/time.js';
import { ValidatorBusyError, type ApiKeyValidator } from './apiKeyValidator.js';
import {
  AUTH_METHODS,
  CLIENT_PREFIX,
  CODE_PREFIX,
  SCOPE,
  SUPPORTED_SCOPES,
  TOKEN_FORMAT_VERSION,
  type ClientAuthMethod,
  type ClientPayload,
  type CodePayload,
} from './oauthTokens.js';
import { pageHeaders, renderAuthorizePage, renderErrorPage } from './pages.js';
import { asString, unprefix } from './params.js';
import type { Sealer } from './sealer.js';
import { registerTokenEndpoint } from './tokenEndpoint.js';

const CODE_TTL = 5 * 60;
const MAX_REDIRECT_URIS = 10;
const MAX_REDIRECT_URI_LENGTH = 2048;

export interface OAuthOptions {
  issuer: URL;
  sealer: Sealer;
  validator: ApiKeyValidator;
  replayStore: ReplayStore;
  allowedRedirectHosts: string[];
}

export function buildOAuthMetadata(issuer: URL): OAuthMetadata {
  const endpoint = (path: string) => new URL(path, issuer).href;
  return {
    authorization_response_iss_parameter_supported: true,
    issuer: issuer.origin,
    authorization_endpoint: endpoint('/authorize'),
    token_endpoint: endpoint('/token'),
    registration_endpoint: endpoint('/register'),
    response_types_supported: ['code'],
    grant_types_supported: ['authorization_code', 'refresh_token'],
    code_challenge_methods_supported: ['S256'],
    token_endpoint_auth_methods_supported: [...AUTH_METHODS],
    scopes_supported: [...SUPPORTED_SCOPES],
  };
}

function validateRedirectUri(raw: string, allowedHosts: string[]): string | null {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return `"${raw}" is not a valid URL`;
  }
  if (url.hash || url.username || url.password) {
    return 'redirect URI must not contain a fragment or credentials';
  }
  const hostname = url.hostname.toLowerCase();
  const isLoopback = isLoopbackHost(hostname);
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && isLoopback)) {
    return 'redirect URI must use https (http is allowed only for localhost)';
  }
  if (!allowedHosts.includes('*') && !allowedHosts.includes(hostname)) {
    return `redirect host "${hostname}" is not allowed by OAUTH_ALLOWED_REDIRECT_HOSTS`;
  }
  return null;
}

type AuthorizeResolution =
  | { kind: 'page-error'; message: string }
  | { kind: 'redirect-error'; redirectUri: string; error: string; description: string; state?: string }
  | {
      kind: 'ok';
      client: ClientPayload;
      clientId: string;
      redirectUri: string;
      isRedirectUriRequired: boolean;
      codeChallenge: string;
      state?: string;
      hiddenFields: Record<string, string>;
    };

type AuthorizeRequest = Extract<AuthorizeResolution, { kind: 'ok' }>;

function redirectError(
  redirectUri: string,
  state: string | undefined,
  error: string,
  description: string,
): AuthorizeResolution {
  return { kind: 'redirect-error', redirectUri, state, error, description };
}

function resolveAuthorize(
  params: Record<string, unknown>,
  getClient: (clientId: unknown) => ClientPayload | null,
): AuthorizeResolution {
  const clientId = asString(params.client_id);
  const client = getClient(clientId);
  if (!clientId || !client) {
    return {
      kind: 'page-error',
      message: 'Unknown client. Remove the connector in your MCP client and add it again.',
    };
  }

  const requestedRedirect = asString(params.redirect_uri);
  const redirectUri = requestedRedirect ?? (client.redirectUris.length === 1 ? client.redirectUris[0] : undefined);
  if (!redirectUri || !client.redirectUris.includes(redirectUri)) {
    return { kind: 'page-error', message: 'The redirect URI does not match the registered client.' };
  }

  const state = asString(params.state);
  if (params.response_type !== 'code') {
    return redirectError(redirectUri, state, 'unsupported_response_type', 'Only response_type=code is supported');
  }
  const codeChallenge = asString(params.code_challenge);
  if (!codeChallenge || !/^[A-Za-z0-9_-]{43}$/.test(codeChallenge) || params.code_challenge_method !== 'S256') {
    return redirectError(redirectUri, state, 'invalid_request', 'PKCE with code_challenge_method=S256 is required');
  }
  const scopes = typeof params.scope === 'string' ? params.scope.split(' ').filter(Boolean) : [];
  if (
    params.scope !== undefined &&
    (typeof params.scope !== 'string' || !scopes.every((scope) => SUPPORTED_SCOPES.includes(scope)))
  ) {
    return redirectError(redirectUri, state, 'invalid_scope', `Supported scopes: ${SUPPORTED_SCOPES.join(' ')}`);
  }

  const hiddenFields: Record<string, string> = {
    response_type: 'code',
    client_id: clientId,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  };
  if (requestedRedirect) {
    hiddenFields.redirect_uri = redirectUri;
  }
  for (const optional of ['state', 'scope', 'resource'] as const) {
    const value = asString(params[optional]);
    if (value) {
      hiddenFields[optional] = value;
    }
  }

  return {
    kind: 'ok',
    client,
    clientId,
    redirectUri,
    isRedirectUriRequired: requestedRedirect !== undefined,
    codeChallenge,
    state,
    hiddenFields,
  };
}

function sendHtml(res: Response, status: number, html: string) {
  res
    .status(status)
    .set({ 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', ...pageHeaders() })
    .send(html);
}

function authorizePage({ client, redirectUri, hiddenFields }: AuthorizeRequest, error?: string): string {
  return renderAuthorizePage({ clientName: client.name, redirectHost: new URL(redirectUri).host, hiddenFields, error });
}

function redirectWith(res: Response, issuer: URL, redirectUri: string, params: Record<string, string | undefined>) {
  const target = new URL(redirectUri);
  for (const [key, value] of Object.entries({ ...params, iss: issuer.origin })) {
    if (value !== undefined) {
      target.searchParams.set(key, value);
    }
  }
  res.redirect(302, target.href);
}

function handleAuthorizeResolution(
  res: Response,
  issuer: URL,
  resolution: AuthorizeResolution,
): resolution is AuthorizeRequest {
  if (resolution.kind === 'page-error') {
    sendHtml(res, 400, renderErrorPage(resolution.message));
    return false;
  }
  if (resolution.kind === 'redirect-error') {
    redirectWith(res, issuer, resolution.redirectUri, {
      error: resolution.error,
      error_description: resolution.description,
      state: resolution.state,
    });
    return false;
  }
  return true;
}

export function createOAuthRouter({
  issuer,
  sealer,
  validator,
  replayStore,
  allowedRedirectHosts,
}: OAuthOptions): Router {
  const router = Router();
  const getClient = (clientId: unknown): ClientPayload | null => {
    const sealed = unprefix(clientId, CLIENT_PREFIX);
    return sealed === null ? null : sealer.open<ClientPayload>('client', sealed);
  };

  router.post('/register', express.json(), (req: Request, res: Response) => {
    const body = (req.body ?? {}) as Record<string, unknown>;
    const redirectUris = body.redirect_uris;
    if (
      !Array.isArray(redirectUris) ||
      !redirectUris.length ||
      redirectUris.length > MAX_REDIRECT_URIS ||
      !redirectUris.every((uri) => typeof uri === 'string' && uri.length <= MAX_REDIRECT_URI_LENGTH)
    ) {
      res.status(400).json({
        error: 'invalid_redirect_uri',
        error_description: `redirect_uris must be 1-${MAX_REDIRECT_URIS} URIs of up to ${MAX_REDIRECT_URI_LENGTH} characters`,
      });
      return;
    }
    for (const uri of redirectUris) {
      const problem = validateRedirectUri(uri, allowedRedirectHosts);
      if (problem) {
        res.status(400).json({ error: 'invalid_redirect_uri', error_description: problem });
        return;
      }
    }

    const authMethod = (asString(body.token_endpoint_auth_method) ?? 'none') as ClientAuthMethod;
    if (!AUTH_METHODS.includes(authMethod)) {
      res.status(400).json({
        error: 'invalid_client_metadata',
        error_description: `token_endpoint_auth_method must be one of ${AUTH_METHODS.join(', ')}`,
      });
      return;
    }

    const isConfidential = authMethod !== 'none';
    const name = (asString(body.client_name) ?? 'MCP client').slice(0, 100);
    const clientId =
      CLIENT_PREFIX +
      sealer.seal<ClientPayload>('client', {
        name,
        redirectUris,
        confidential: isConfidential,
        authMethod,
      });

    res.status(201).json({
      client_id: clientId,
      client_id_issued_at: nowSeconds(),
      ...(isConfidential ? { client_secret: sealer.sign(clientId), client_secret_expires_at: 0 } : {}),
      client_name: name,
      redirect_uris: redirectUris,
      grant_types: ['authorization_code', 'refresh_token'],
      response_types: ['code'],
      token_endpoint_auth_method: authMethod,
      scope: SCOPE,
    });
  });

  router.get('/authorize', (req: Request, res: Response) => {
    const resolution = resolveAuthorize(req.query as Record<string, unknown>, getClient);
    if (!handleAuthorizeResolution(res, issuer, resolution)) {
      return;
    }
    sendHtml(res, 200, authorizePage(resolution));
  });

  router.post('/authorize', express.urlencoded({ extended: false }), async (req: Request, res: Response) => {
    const body = (req.body ?? {}) as Record<string, unknown>;
    const resolution = resolveAuthorize(body, getClient);
    if (!handleAuthorizeResolution(res, issuer, resolution)) {
      return;
    }

    const rerender = (error: string) => sendHtml(res, 400, authorizePage(resolution, error));

    const apiKey = asString(body.api_key)?.trim();
    if (!apiKey) {
      rerender('Enter your Pneumatic API key.');
      return;
    }

    let user;
    try {
      user = await validator.validate(apiKey);
    } catch (error) {
      rerender(
        error instanceof ValidatorBusyError
          ? 'Too many sign-in attempts right now. Try again in a minute.'
          : 'Could not reach Pneumatic to verify the key. Try again in a moment.',
      );
      return;
    }
    if (!user) {
      res.locals.keyRejected = true;
      rerender('This API key was rejected by Pneumatic. Check that it is copied completely and still active.');
      return;
    }

    const code =
      CODE_PREFIX +
      sealer.seal<CodePayload>(
        'code',
        {
          version: TOKEN_FORMAT_VERSION,
          clientId: resolution.clientId,
          redirectUri: resolution.redirectUri,
          redirectUriRequired: resolution.isRedirectUriRequired,
          codeChallenge: resolution.codeChallenge,
          apiKey,
          jti: randomBytes(16).toString('base64url'),
        },
        CODE_TTL,
      );
    redirectWith(res, issuer, resolution.redirectUri, { code, state: resolution.state });
  });

  registerTokenEndpoint(router, { sealer, validator, replayStore, getClient });

  return router;
}

import { createHash, randomBytes } from 'node:crypto';

import express, { type Request, type Response, type Router } from 'express';

import type { ReplayStore } from '../core/ports.js';
import { nowSeconds } from '../core/time.js';
import type { ApiKeyValidator } from './apiKeyValidator.js';
import {
  ACCESS_PREFIX,
  ACCESS_TOKEN_TTL,
  CODE_PREFIX,
  REFRESH_PREFIX,
  s256,
  SCOPE,
  TOKEN_FORMAT_VERSION,
  type ClientPayload,
  type CodePayload,
  type TokenPayload,
} from './oauthTokens.js';
import { asString, unprefix } from './params.js';
import type { Sealer } from './sealer.js';

const REFRESH_TOKEN_TTL = 90 * 24 * 60 * 60;
// A client retrying a lost refresh response is not a theft signal; only later reuse revokes the session.
const REUSE_GRACE_SECONDS = 30;

export interface TokenEndpointOptions {
  sealer: Sealer;
  validator: ApiKeyValidator;
  replayStore: ReplayStore;
  getClient: (clientId: unknown) => ClientPayload | null;
}

type TokenRequest = Record<string, unknown>;
type TokenResponse = ReturnType<typeof issueTokens>;

interface TokenError {
  status: number;
  error: string;
  description: string;
}

function tokenError(status: number, error: string, description: string): TokenError {
  return { status, error, description };
}

// Every token issued from one authorization shares a family, so a replayed refresh token revokes the chain.
function issueTokens(
  sealer: Sealer,
  clientId: string,
  apiKey: string,
  familyId = randomBytes(16).toString('base64url'),
) {
  return {
    access_token: ACCESS_PREFIX + sealer.seal<TokenPayload>('access', { clientId, apiKey, familyId }, ACCESS_TOKEN_TTL),
    token_type: 'Bearer',
    expires_in: ACCESS_TOKEN_TTL,
    refresh_token:
      REFRESH_PREFIX +
      sealer.seal<TokenPayload>(
        'refresh',
        { clientId, apiKey, version: TOKEN_FORMAT_VERSION, familyId },
        REFRESH_TOKEN_TTL,
      ),
    scope: SCOPE,
  };
}

function authenticateClient(
  { sealer, getClient }: TokenEndpointOptions,
  authorization: string | undefined,
  body: TokenRequest,
): { clientId: string } | TokenError {
  let clientId = asString(body.client_id);
  let clientSecret = asString(body.client_secret);
  const basic = authorization?.match(/^Basic\s+(.+)$/i)?.[1];
  if (basic) {
    const decoded = Buffer.from(basic, 'base64').toString('utf8');
    const separator = decoded.indexOf(':');
    if (separator < 1) {
      return tokenError(401, 'invalid_client', 'Malformed Basic authorization header');
    }
    try {
      clientId = decodeURIComponent(decoded.slice(0, separator));
      clientSecret = decodeURIComponent(decoded.slice(separator + 1));
    } catch {
      return tokenError(401, 'invalid_client', 'Malformed Basic authorization header');
    }
  }

  const client = getClient(clientId);
  if (!clientId || !client) {
    return tokenError(401, 'invalid_client', 'Unknown client');
  }
  if (client.confidential && !client.authMethod) {
    return tokenError(401, 'invalid_client', 'Client must register again to use the token endpoint');
  }
  if (
    (client.authMethod === 'client_secret_basic' && (!basic || body.client_secret !== undefined)) ||
    (client.authMethod === 'client_secret_post' && basic) ||
    (client.confidential && !(clientSecret && sealer.verifySignature(clientId, clientSecret)))
  ) {
    return tokenError(401, 'invalid_client', 'Client authentication failed');
  }
  return { clientId };
}

async function exchangeCode(
  { sealer, replayStore }: TokenEndpointOptions,
  body: TokenRequest,
  clientId: string,
): Promise<TokenResponse | TokenError> {
  const sealedCode = unprefix(body.code, CODE_PREFIX);
  const code = sealedCode === null ? null : sealer.open<CodePayload>('code', sealedCode);
  if (!code?.exp || code.version !== TOKEN_FORMAT_VERSION || code.clientId !== clientId) {
    return tokenError(400, 'invalid_grant', 'Authorization code is invalid or expired');
  }
  const redirectUri = asString(body.redirect_uri);
  if ((code.redirectUriRequired && !redirectUri) || (redirectUri && redirectUri !== code.redirectUri)) {
    return tokenError(400, 'invalid_grant', 'redirect_uri does not match the authorization request');
  }
  const verifier = asString(body.code_verifier);
  if (!verifier || !/^[A-Za-z0-9._~-]{43,128}$/.test(verifier) || s256(verifier) !== code.codeChallenge) {
    return tokenError(400, 'invalid_grant', 'PKCE verification failed');
  }
  if (!(await replayStore.markUsed('code', code.jti, code.exp))) {
    return tokenError(400, 'invalid_grant', 'Authorization code was already used');
  }
  return issueTokens(sealer, clientId, code.apiKey);
}

async function rotateRefresh(
  { sealer, validator, replayStore }: TokenEndpointOptions,
  body: TokenRequest,
  clientId: string,
): Promise<TokenResponse | TokenError> {
  const sealedRefresh = unprefix(body.refresh_token, REFRESH_PREFIX);
  const refresh = sealedRefresh === null ? null : sealer.open<TokenPayload>('refresh', sealedRefresh);
  if (
    sealedRefresh === null ||
    !refresh?.exp ||
    refresh.version !== TOKEN_FORMAT_VERSION ||
    refresh.clientId !== clientId
  ) {
    return tokenError(400, 'invalid_grant', 'Refresh token is invalid or expired');
  }
  if (refresh.familyId && (await replayStore.isUsed('family', refresh.familyId))) {
    return tokenError(400, 'invalid_grant', 'Refresh token was revoked after reuse');
  }
  try {
    if (!(await validator.validate(refresh.apiKey))) {
      return tokenError(400, 'invalid_grant', 'Pneumatic API key was revoked');
    }
  } catch {
    return tokenError(503, 'temporarily_unavailable', 'Could not reach Pneumatic');
  }
  const tokenId = createHash('sha256').update(Buffer.from(sealedRefresh, 'base64url')).digest('hex');
  // The grace mark precedes the refresh entry, so only a spent token without a live mark is a late replay.
  const isFirstWithinGrace = await replayStore.markUsed('rotation', tokenId, nowSeconds() + REUSE_GRACE_SECONDS);
  if (!(await replayStore.markUsed('refresh', tokenId, refresh.exp))) {
    const isGraceful = !isFirstWithinGrace;
    if (refresh.familyId && !isGraceful) {
      await replayStore.markUsed('family', refresh.familyId, nowSeconds() + REFRESH_TOKEN_TTL);
    }
    return tokenError(
      400,
      'invalid_grant',
      isGraceful ? 'Refresh token was already used' : 'Refresh token was already used; the session was revoked',
    );
  }
  return issueTokens(sealer, clientId, refresh.apiKey, refresh.familyId);
}

async function grantTokens(
  options: TokenEndpointOptions,
  authorization: string | undefined,
  body: TokenRequest,
): Promise<TokenResponse | TokenError> {
  const client = authenticateClient(options, authorization, body);
  if ('error' in client) {
    return client;
  }
  if (body.grant_type === 'authorization_code') {
    return exchangeCode(options, body, client.clientId);
  }
  if (body.grant_type === 'refresh_token') {
    return rotateRefresh(options, body, client.clientId);
  }
  return tokenError(400, 'unsupported_grant_type', 'Supported grant types: authorization_code, refresh_token');
}

export function registerTokenEndpoint(router: Router, options: TokenEndpointOptions) {
  router.post('/token', express.urlencoded({ extended: false }), async (req: Request, res: Response) => {
    res.set('Cache-Control', 'no-store');
    const body = (req.body ?? {}) as TokenRequest;
    const result = await grantTokens(options, req.headers.authorization, body);
    if ('error' in result) {
      res.status(result.status).json({ error: result.error, error_description: result.description });
      return;
    }
    res.json(result);
  });
}

import { createHash } from 'node:crypto';

import { OAuthError, OAuthErrorCode, type AuthInfo, type OAuthTokenVerifier } from '@modelcontextprotocol/server';

import type { ReplayStore } from '../core/ports.js';
import { nowSeconds } from '../core/time.js';
import { ValidatorBusyError, type ApiKeyValidator } from './apiKeyValidator.js';
import { unprefix } from './params.js';
import type { Sealer } from './sealer.js';

export const SCOPE = 'pneumatic';
export const SUPPORTED_SCOPES: readonly string[] = [SCOPE, 'offline_access'];

export const ACCESS_TOKEN_TTL = 60 * 60;

export const TOKEN_FORMAT_VERSION = 1;
export const CLIENT_PREFIX = 'pmcp_c_';
export const CODE_PREFIX = 'pmcp_code_';
export const ACCESS_PREFIX = 'pmcp_at_';
export const REFRESH_PREFIX = 'pmcp_rt_';

export const AUTH_METHODS = ['none', 'client_secret_post', 'client_secret_basic'] as const;
export type ClientAuthMethod = (typeof AUTH_METHODS)[number];

// Sealed into issued client IDs and codes, so renaming a payload field breaks existing connections.
export interface ClientPayload {
  name: string;
  redirectUris: string[];
  confidential: boolean;
  authMethod?: ClientAuthMethod;
}

export interface CodePayload {
  version?: number;
  clientId: string;
  redirectUri: string;
  redirectUriRequired?: boolean;
  codeChallenge: string;
  apiKey: string;
  jti: string;
}

export interface TokenPayload {
  clientId: string;
  apiKey: string;
  version?: number;
  familyId?: string;
}

export function s256(verifier: string): string {
  return createHash('sha256').update(verifier).digest('base64url');
}

export function createTokenVerifier(
  sealer: Sealer,
  validator: ApiKeyValidator,
  replayStore: ReplayStore,
): OAuthTokenVerifier {
  return {
    async verifyAccessToken(token: string): Promise<AuthInfo> {
      let tokenPayload: TokenPayload;
      let expiresAt: number;

      const sealed = unprefix(token, ACCESS_PREFIX);
      if (sealed !== null) {
        const opened = sealer.open<TokenPayload>('access', sealed);
        if (!opened?.exp || (opened.familyId && (await replayStore.isUsed('family', opened.familyId)))) {
          throw new OAuthError(OAuthErrorCode.InvalidToken, 'Access token is invalid, expired or revoked');
        }
        tokenPayload = opened;
        expiresAt = opened.exp;
      } else if (token.startsWith('pmcp_')) {
        throw new OAuthError(OAuthErrorCode.InvalidToken, 'Not an access token');
      } else {
        // Static Bearer credentials bypass OAuth but must still validate against Pneumatic.
        tokenPayload = { clientId: 'api-key', apiKey: token };
        expiresAt = nowSeconds() + ACCESS_TOKEN_TTL;
      }

      let user;
      try {
        user = await validator.validate(tokenPayload.apiKey);
      } catch (error) {
        if (error instanceof ValidatorBusyError) {
          throw new OAuthError(OAuthErrorCode.ServerError, 'Too many API key checks right now; retry in a minute');
        }
        throw error;
      }
      if (!user) {
        throw new OAuthError(OAuthErrorCode.InvalidToken, 'Pneumatic API key is invalid or revoked');
      }
      return {
        token,
        clientId: tokenPayload.clientId,
        scopes: [SCOPE],
        expiresAt,
        extra: { apiKey: tokenPayload.apiKey, userId: user.id },
      };
    },
  };
}

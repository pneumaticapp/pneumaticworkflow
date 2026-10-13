import { NextFunction, Request, Response } from 'express';
import { ERoutes } from '../../public/constants/routes';
import { getConfig } from '../../public/utils/getConfig';
import { isMcpId, mcpContinuation } from '../../public/utils/safeRedirect';
import { IMcpConnection, IMcpIdentity, IMcpUploadSession, TMcpUploadStatus } from '../../public/types/mcp';
import { IAuthenticatedUser } from '../utils/types';
import { mcpCore, McpCoreError } from '../utils/mcpCore';
import {
  clearMcpContinuation,
  issueMcpCsrf,
  mcpCookies,
  mcpEnabled,
  mcpLoginRedirect,
  mcpPrivacy,
  rememberMcpContinuation,
  validMcpCsrf,
} from '../utils/mcpSecurity';

type TMcpUser = IAuthenticatedUser & { token: string };
type TMcpHandler = (req: Request, res: Response, user: TMcpUser) => Promise<unknown>;

function fail(res: Response, status: number) {
  const message = status === 403 ? 'Permission denied' : status === 502 ? 'MCP request failed' : 'Invalid MCP request';
  return res.status(status).json({
    message,
    code: status === 403 ? 'permission_denied' : status === 502 ? 'unavailable' : 'invalid_request',
    details: { name: 'request', reason: message },
  });
}

function assertIdentity(value: IMcpIdentity, user: TMcpUser) {
  if (
    !value ||
    !['string', 'number'].includes(typeof value.user_id) ||
    !['string', 'number'].includes(typeof value.account_id) ||
    String(value.user_id) !== String(user.id) ||
    String(value.account_id) !== String(user.account.id)
  )
    throw new McpCoreError(403);
}

function scopes(value: unknown): string[] {
  if (
    !Array.isArray(value) ||
    !value.every((scope) => ['pneumatic:read', 'pneumatic:write', 'files:read', 'files:write'].includes(scope))
  ) {
    throw new McpCoreError(502);
  }
  return value;
}

export const guardMcp =
  (handler: TMcpHandler, page = false) =>
  async (req: Request, res: Response) => {
    mcpPrivacy(res);
    if (!mcpEnabled()) return fail(res, 404);
    const token = mcpCookies(req).token;
    if (!token) {
      if (!page) return fail(res, 401);
      const target = mcpContinuation(req.originalUrl);
      if (!target) return fail(res, 400);
      rememberMcpContinuation(res, target);
      return res.redirect(`${ERoutes.Login}?redirectUrl=${encodeURIComponent(target)}`);
    }
    if (req.method !== 'GET' && !validMcpCsrf(req, token)) return fail(res, 403);
    try {
      // Do not use cached user context: deactivation and account changes apply immediately.
      const context = await mcpCore<IAuthenticatedUser>('GET', getConfig().api.urls.getUser, token);
      if (!context.id || !context.account?.id || context.account.is_blocked) return fail(res, 403);
      return await handler(req, res, { ...context, token });
    } catch (error) {
      const status = error instanceof McpCoreError ? error.status : 502;
      if (page && status === 401) {
        const target = mcpContinuation(req.originalUrl);
        if (!target) return fail(res, 400);
        rememberMcpContinuation(res, target);
        res.clearCookie('token', { domain: req.hostname, path: '/' });
        return res.redirect(`${ERoutes.Login}?redirectUrl=${encodeURIComponent(target)}`);
      }
      return fail(res, status);
    }
  };

export function mcpPage(req: Request, res: Response, next: NextFunction) {
  if (!mcpContinuation(req.originalUrl)) {
    mcpPrivacy(res);
    return fail(res, 400);
  }
  return guardMcp(async (_, response, user) => {
    // Existing main rendering must not serialize the bearer credential for MCP pages.
    const { token, ...identity } = user;
    response.locals.user = identity;
    clearMcpContinuation(response);
    next();
  }, true)(req, res);
}

export const mcpConsentContext = guardMcp(async (req, res, user) => {
  const requestId = req.query.request_id;
  if (!isMcpId(requestId) || Object.keys(req.query).some((key) => key !== 'request_id')) return fail(res, 400);
  const data = await mcpCore<
    IMcpIdentity & {
      request_id: string;
      client: { id: string; name: string };
      account: { id: number; name: string };
      scopes: string[];
      expires_at: string;
      login_complete: boolean;
    }
  >('GET', `/integrations/mcp/consent?request_id=${encodeURIComponent(requestId)}`, user.token);
  assertIdentity(data, user);
  if (
    typeof data.request_id !== 'string' ||
    data.request_id.toLowerCase() !== requestId.toLowerCase() ||
    String(data.account?.id) !== String(user.account.id) ||
    typeof data.client?.name !== 'string' ||
    typeof data.account?.name !== 'string' ||
    data.client.name.length > 256 ||
    data.account.name.length > 256 ||
    typeof data.login_complete !== 'boolean'
  )
    throw new McpCoreError(502);
  if (typeof data.expires_at !== 'string' || !Number.isFinite(Date.parse(data.expires_at))) throw new McpCoreError(502);
  if (Date.parse(data.expires_at) <= Date.now()) throw new McpCoreError(410);
  return res.json({
    request_id: requestId,
    client_name: data.client.name,
    account_name: data.account.name,
    scopes: scopes(data.scopes),
    login_complete: data.login_complete === true,
    csrf_token: issueMcpCsrf(req, res, user.token),
  });
});

export const mcpConnect = guardMcp(async (req, res, user) => {
  const requestId = req.body?.request_id;
  if (!isMcpId(requestId) || Object.keys(req.body).some((key) => key !== 'request_id')) return fail(res, 400);
  const result = await mcpCore<{ code: string; request_id: string; expires_in: number }>(
    'POST',
    '/integrations/mcp/login-code',
    user.token,
    { request_id: requestId },
  );
  return res.json({ redirect_url: mcpLoginRedirect(result, requestId) });
});

export const mcpApprove = guardMcp(async (req, res, user) => {
  const { request_id: requestId, allow } = req.body || {};
  if (
    !isMcpId(requestId) ||
    typeof allow !== 'boolean' ||
    Object.keys(req.body).some((key) => !['request_id', 'allow'].includes(key))
  )
    return fail(res, 400);
  const result = await mcpCore<{ code: string; request_id: string; expires_in: number }>(
    'POST',
    '/integrations/mcp/consent',
    user.token,
    { request_id: requestId, allow },
  );
  return res.json({ redirect_url: mcpLoginRedirect(result, requestId) });
});

async function connections(user: TMcpUser) {
  const data = await mcpCore<{ results: IMcpConnection[] }>('GET', '/integrations/mcp/connections', user.token);
  if (!Array.isArray(data.results)) throw new McpCoreError(502);
  return data.results.map((item) => {
    assertIdentity(item, user);
    if (
      !isMcpId(item.id) ||
      typeof item.client_name !== 'string' ||
      item.client_name.length > 256 ||
      typeof item.created_at !== 'string' ||
      !Number.isFinite(Date.parse(item.created_at)) ||
      (item.revoked_at !== null &&
        (typeof item.revoked_at !== 'string' || !Number.isFinite(Date.parse(item.revoked_at))))
    )
      throw new McpCoreError(502);
    return {
      id: item.id,
      client_name: item.client_name,
      scopes: scopes(item.scopes),
      created_at: item.created_at,
      revoked_at: item.revoked_at,
      user_id: item.user_id,
      account_id: item.account_id,
    };
  });
}

export const mcpConnections = guardMcp(async (req, res, user) =>
  res.json({
    results: await connections(user),
    csrf_token: issueMcpCsrf(req, res, user.token),
  }),
);

export const mcpRevoke = guardMcp(async (req, res, user) => {
  const id = req.params.connection_id.toLowerCase();
  if (!isMcpId(id) || Object.keys(req.body || {}).length) return fail(res, 400);
  const item = (await connections(user)).find((connection) => connection.id === id);
  if (!item) return fail(res, 404);
  if (!item.revoked_at) await mcpCore('DELETE', `/integrations/mcp/connections/${encodeURIComponent(id)}`, user.token);
  return res.status(204).end();
});

const UPLOAD_STATUSES: TMcpUploadStatus[] = [
  'pending',
  'importing',
  'ready',
  'attached',
  'expired',
  'revoked',
  'failed',
];
async function uploadSession(id: string, user: TMcpUser) {
  if (!isMcpId(id)) throw new McpCoreError(400);
  id = id.toLowerCase();
  const data = await mcpCore<IMcpUploadSession>(
    'GET',
    `/integrations/mcp/uploads/${encodeURIComponent(id)}`,
    user.token,
  );
  assertIdentity(data, user);
  if (
    data.id !== id ||
    !UPLOAD_STATUSES.includes(data.status) ||
    typeof data.expires_at !== 'string' ||
    !Number.isFinite(Date.parse(data.expires_at)) ||
    typeof data.filename !== 'string' ||
    typeof data.content_type !== 'string' ||
    !Number.isSafeInteger(data.size) ||
    data.size < 1
  )
    throw new McpCoreError(502);
  if (
    ['expired', 'revoked', 'failed'].includes(data.status) ||
    (data.status !== 'attached' && Date.parse(data.expires_at) <= Date.now())
  )
    throw new McpCoreError(410);
  return {
    id: data.id,
    status: data.status,
    filename: data.filename,
    content_type: data.content_type,
    size: data.size,
    expires_at: data.expires_at,
    user_id: data.user_id,
    account_id: data.account_id,
  };
}

export const mcpUploadSession = guardMcp(async (req, res, user) =>
  res.json({
    session: await uploadSession(req.params.session_id, user),
    csrf_token: issueMcpCsrf(req, res, user.token),
  }),
);

export const mcpUploadToken = guardMcp(async (req, res, user) => {
  if (Object.keys(req.body || {}).length) return fail(res, 400);
  const session = await uploadSession(req.params.session_id, user);
  if (session.status !== 'pending') return fail(res, 409);
  const result = await mcpCore<{
    access_token: string;
    token_type: string;
    expires_in: number;
    file_upload_url: string;
    upload_session_id: string;
  }>('POST', `/integrations/mcp/uploads/${encodeURIComponent(session.id)}/token`, user.token, {});
  const uploadUrl = new URL('/files/upload', getConfig().host).href;
  if (
    result.upload_session_id !== session.id ||
    result.file_upload_url !== uploadUrl ||
    result.token_type !== 'Bearer' ||
    typeof result.access_token !== 'string' ||
    !/^mcp-u_[A-Za-z0-9_-]{16,512}$/.test(result.access_token) ||
    !Number.isFinite(result.expires_in) ||
    result.expires_in <= 0 ||
    result.expires_in > 300
  )
    throw new McpCoreError(502);
  return res.json({
    access_token: result.access_token,
    upload_session_id: session.id,
    file_upload_url: uploadUrl,
    expires_in: result.expires_in,
  });
});

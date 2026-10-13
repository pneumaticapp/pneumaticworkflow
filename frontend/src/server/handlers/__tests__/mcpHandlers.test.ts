// <reference types="jest" />
import { createHmac } from 'crypto';
import { Request, Response } from 'express';
import {
  mcpApprove,
  mcpConnect,
  mcpConsentContext,
  mcpConnections,
  mcpPage,
  mcpRevoke,
  mcpUploadSession,
  mcpUploadToken,
} from '../mcpHandlers';
import { mcpCore, McpCoreError } from '../../utils/mcpCore';

jest.mock('../../../public/utils/getConfig', () => ({
  getConfig: () => ({ env: 'prod', host: 'https://my.pneumatic.app', api: { urls: { getUser: '/auth/context' } } }),
}));
jest.mock('../../utils/mcpCore', () => ({
  ...jest.requireActual('../../utils/mcpCore'),
  mcpCore: jest.fn(),
}));

describe('MCP handlers', () => {
  const ID = '550e8400-e29b-41d4-a716-446655440000';
  const TOKEN = 'cookie-session';
  const NONCE = 'a'.repeat(64);
  const CSRF = createHmac('sha256', TOKEN).update(NONCE).digest('hex');
  const core = mcpCore as jest.Mock;
  const makeUser = () => ({ id: 7, account: { id: 9, is_blocked: false } });
  const makeSession = (overrides: Record<string, unknown> = {}) => ({
    id: ID,
    user_id: 7,
    account_id: 9,
    status: 'pending',
    filename: 'report.pdf',
    size: 4096,
    content_type: 'application/pdf',
    expires_at: '2099-01-01T00:00:00Z',
    ...overrides,
  });
  const makeConnection = (overrides: Record<string, unknown> = {}) => ({
    id: ID,
    user_id: 7,
    account_id: 9,
    client_name: 'Assistant',
    scopes: ['pneumatic:read'],
    created_at: '2026-10-09T00:00:00Z',
    revoked_at: null,
    ...overrides,
  });
  const makeConsent = (overrides: Record<string, unknown> = {}) => ({
    request_id: ID,
    user_id: 7,
    account_id: 9,
    client: { id: 'client', name: 'Assistant' },
    account: { id: 9, name: 'My account' },
    scopes: ['pneumatic:read', 'files:write'],
    expires_at: '2099-01-01T00:00:00Z',
    login_complete: false,
    ...overrides,
  });
  const makeToken = (overrides: Record<string, unknown> = {}) => ({
    access_token: `mcp-u_${'b'.repeat(32)}`,
    token_type: 'Bearer',
    expires_in: 300,
    upload_session_id: ID,
    file_upload_url: 'https://my.pneumatic.app/files/upload',
    ...overrides,
  });
  const makeReq = (overrides: Record<string, unknown> = {}) => {
    const headers: Record<string, string> = {
      cookie: `token=${TOKEN}; mcp-csrf=${NONCE}`,
      origin: 'https://my.pneumatic.app',
      'x-mcp-csrf': CSRF,
      'sec-fetch-site': 'same-origin',
    };
    return {
      method: 'POST',
      body: {},
      query: {},
      params: { session_id: ID, connection_id: ID },
      originalUrl: `/mcp/connect?request_id=${ID}`,
      hostname: 'my.pneumatic.app',
      get: (name: string) => headers[name.toLowerCase()],
      ...overrides,
    } as unknown as Request;
  };
  const makeRes = () => {
    const res = {
      status: jest.fn(),
      json: jest.fn(),
      redirect: jest.fn(),
      end: jest.fn(),
      setHeader: jest.fn(),
      cookie: jest.fn(),
      clearCookie: jest.fn(),
      locals: {},
    };
    res.status.mockReturnValue(res);
    return res;
  };
  const call = async (handler: (req: Request, res: Response) => unknown, req: Request = makeReq()) => {
    const res = makeRes();
    await handler(req, res as unknown as Response);
    return res;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    core.mockReset();
    process.env.MCP_ENABLED = 'yes';
    process.env.MCP_PUBLIC_URL = 'https://my.pneumatic.app/mcp';
    core.mockResolvedValueOnce(makeUser());
  });

  it.each(['no', 'true', 'false', '1', 'YES', '', undefined])(
    'test_mcpConnect__fails_closed_for_MCP_ENABLED_%p__ok',
    async (value) => {
      // arrange
      if (value === undefined) delete process.env.MCP_ENABLED;
      else process.env.MCP_ENABLED = value;

      // act
      const res = await call(mcpConnect);

      // assert
      expect(res.status).toHaveBeenCalledWith(404);
      expect(core).not.toHaveBeenCalled();
    },
  );
  it('test_mcpConnect__uses_cookie_auth_and_ignores_a_query_or_header_bearer__ok', async () => {
    // arrange

    // act
    const res = await call(mcpConnect, makeReq({ get: () => undefined, query: { mobile_app_token: TOKEN } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(401);
    expect(core).not.toHaveBeenCalled();
  });
  it.each(['missing', 'cross-origin', 'cross-site', 'forged', 'changed-user'])(
    'test_mcpConnect__blocks_%s_CSRF_before_calling_core__rejects',
    async (kind) => {
      // arrange
      const headers: Record<string, string> = {
        cookie: `token=${TOKEN}; mcp-csrf=${NONCE}`,
        origin: 'https://my.pneumatic.app',
        'x-mcp-csrf': CSRF,
        'sec-fetch-site': 'same-origin',
      };
      if (kind === 'missing') delete headers['x-mcp-csrf'];
      if (kind === 'cross-origin') headers.origin = 'https://evil.example';
      if (kind === 'cross-site') headers['sec-fetch-site'] = 'cross-site';
      if (kind === 'forged') headers['x-mcp-csrf'] = 'b'.repeat(64);
      if (kind === 'changed-user') headers.cookie = `token=another-user; mcp-csrf=${NONCE}`;

      // act
      const res = await call(mcpConnect, makeReq({ body: { request_id: ID }, get: (name: string) => headers[name] }));

      // assert
      expect(res.status).toHaveBeenCalledWith(403);
      expect(core).not.toHaveBeenCalled();
    },
  );
  it.each([
    '../secret',
    `${ID}?redirectUrl=https://evil.example`,
    [ID, ID],
    '%2f%2fevil',
    'not-a-uuid',
    '',
    null,
    undefined,
    17,
  ])('test_mcpConnect__rejects_a_malicious_request_ID_%p__rejects', async (request_id) => {
    // arrange

    // act
    const res = await call(mcpConnect, makeReq({ body: { request_id } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(400);
    expect(core).toHaveBeenCalledTimes(1);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
  });
  it('test_mcpConnect__rejects_caller_supplied_redirects__rejects', async () => {
    // arrange

    // act
    const res = await call(mcpConnect, makeReq({ body: { request_id: ID, redirect_url: 'https://evil.example' } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(400);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(1);
  });
  it('test_mcpConnect__bridges_the_cookie_using_explicit_Bearer_and_returns_only__ok', async () => {
    // arrange
    core.mockResolvedValueOnce({
      code: 'one-time-code',
      request_id: ID,
      expires_in: 60,
      token: TOKEN,
      redirect_url: 'https://evil.example',
    });

    // act
    const res = await call(mcpConnect, makeReq({ body: { request_id: ID } }));

    // assert
    expect(core).toHaveBeenCalledWith('POST', '/integrations/mcp/login-code', TOKEN, { request_id: ID });
    expect(res.json).toHaveBeenCalledWith({
      redirect_url: `https://my.pneumatic.app/oauth/mcp/login?code=one-time-code&request_id=${ID}`,
    });
    expect(res.setHeader).toHaveBeenCalledWith('Cache-Control', 'no-store');
    expect(res.setHeader).toHaveBeenCalledWith('Referrer-Policy', 'no-referrer');

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'POST', '/integrations/mcp/login-code', TOKEN, { request_id: ID });
  });
  it('test_mcpConnect__rejects_a_login_code_for_another_request__rejects', async () => {
    // arrange
    core.mockResolvedValueOnce({ code: 'code', request_id: 'other', expires_in: 60 });

    // act
    const res = await call(mcpConnect, makeReq({ body: { request_id: ID } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(502);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'POST', '/integrations/mcp/login-code', TOKEN, { request_id: ID });
  });
  it('test_mcpConnect__does_not_expose_expired_or_reused_code_errors_from_co__rejects', async () => {
    // arrange
    core.mockRejectedValueOnce(new McpCoreError(410));

    // act
    const res = await call(mcpConnect, makeReq({ body: { request_id: ID } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(410);
    expect(res.json).toHaveBeenCalledWith({
      message: 'Invalid MCP request',
      code: 'invalid_request',
      details: { name: 'request', reason: 'Invalid MCP request' },
    });

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'POST', '/integrations/mcp/login-code', TOKEN, { request_id: ID });
  });
  it('test_mcpConsentContext__returns_consent_context_with_canonical_permissions__ok', async () => {
    // arrange
    core.mockResolvedValueOnce(makeConsent({ login_complete: true, credential: 'secret' }));

    // act
    const res = await call(mcpConsentContext, makeReq({ method: 'GET', query: { request_id: ID } }));

    // assert
    expect(res.json).toHaveBeenCalledWith({
      request_id: ID,
      login_complete: true,
      client_name: 'Assistant',
      account_name: 'My account',
      scopes: ['pneumatic:read', 'files:write'],
      csrf_token: CSRF,
    });
    expect(res.cookie).toHaveBeenCalledWith(
      'mcp-csrf',
      NONCE,
      expect.objectContaining({ httpOnly: true, secure: true, sameSite: 'strict' }),
    );

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/consent?request_id=${ID}`, TOKEN);
  });
  it.each([
    { user_id: 8 },
    { account_id: 10 },
    { user_id: [7] },
    { account_id: [9] },
    { expires_at: '2000-01-01T00:00:00Z' },
  ])('test_mcpConsentContext__rejects_invalid_consent_ownership_or_expiry_%p__rejects', async (override) => {
    // arrange
    core.mockResolvedValueOnce(makeConsent(override));

    // act
    const res = await call(mcpConsentContext, makeReq({ method: 'GET', query: { request_id: ID } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(override.expires_at ? 410 : 403);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/consent?request_id=${ID}`, TOKEN);
  });

  it.each([
    { client: { name: { html: '<script>bad()</script>' } } },
    { scopes: ['unknown:scope'] },
    { login_complete: 'true' },
  ])('test_mcpConsentContext__rejects_malformed_untrusted_consent_metadata_%__rejects', async (override) => {
    // arrange
    core.mockResolvedValueOnce(makeConsent(override));

    // act
    const res = await call(mcpConsentContext, makeReq({ method: 'GET', query: { request_id: ID } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(502);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/consent?request_id=${ID}`, TOKEN);
  });
  it.each([true, false])('test_mcpApprove__finishes_allow_%s_through_a_fixed_one_time_handoff__ok', async (allow) => {
    // arrange
    core.mockResolvedValueOnce({ code: 'consent-code', request_id: ID, expires_in: 60 });

    // act
    const res = await call(mcpApprove, makeReq({ body: { request_id: ID, allow } }));

    // assert
    expect(core).toHaveBeenCalledWith('POST', '/integrations/mcp/consent', TOKEN, { request_id: ID, allow });
    expect(res.json).toHaveBeenCalledWith({
      redirect_url: `https://my.pneumatic.app/oauth/mcp/login?code=consent-code&request_id=${ID}`,
    });

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'POST', '/integrations/mcp/consent', TOKEN, { request_id: ID, allow });
  });
  it('test_mcpConnections__lists_only_safe_connection_fields__ok', async () => {
    // arrange
    core.mockResolvedValueOnce({ results: [makeConnection({ access_token: 'secret' })] });

    // act
    const res = await call(mcpConnections, makeReq({ method: 'GET' }));

    // assert
    expect(res.json).toHaveBeenCalledWith({ results: [makeConnection()], csrf_token: CSRF });

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', '/integrations/mcp/connections', TOKEN);
  });
  it.each([{ user_id: 8 }, { account_id: 10 }, { user_id: [7] }, { account_id: [9] }])(
    'test_mcpConnections__rejects_foreign_connections_%p__rejects',
    async (override) => {
      // arrange
      core.mockResolvedValueOnce({ results: [makeConnection(override)] });

      // act
      const res = await call(mcpConnections, makeReq({ method: 'GET' }));

      // assert
      expect(res.status).toHaveBeenCalledWith(403);

      expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
      expect(core).toHaveBeenCalledTimes(2);
      expect(core).toHaveBeenNthCalledWith(2, 'GET', '/integrations/mcp/connections', TOKEN);
    },
  );
  it('test_mcpRevoke__revokes_a_connection_owned_by_the_current_cookie_user_and_a__ok', async () => {
    // arrange
    core.mockResolvedValueOnce({ results: [makeConnection()] }).mockResolvedValueOnce(undefined);

    // act
    const res = await call(mcpRevoke, makeReq({ method: 'DELETE' }));

    // assert
    expect(core).toHaveBeenCalledWith('DELETE', `/integrations/mcp/connections/${ID}`, TOKEN);
    expect(res.status).toHaveBeenCalledWith(204);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(3);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', '/integrations/mcp/connections', TOKEN);
    expect(core).toHaveBeenNthCalledWith(3, 'DELETE', `/integrations/mcp/connections/${ID}`, TOKEN);
  });
  it('test_mcpRevoke__does_not_replay_a_revoke_for_an_already_revoked_connec__rejects', async () => {
    // arrange
    core.mockResolvedValueOnce({ results: [makeConnection({ revoked_at: '2026-10-09T00:00:00Z' })] });

    // act
    const res = await call(mcpRevoke, makeReq({ method: 'DELETE' }));

    // assert
    expect(core).toHaveBeenCalledTimes(2);
    expect(res.status).toHaveBeenCalledWith(204);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', '/integrations/mcp/connections', TOKEN);
  });
  it.each(['../other', 'invalid'])(
    'test_mcpUploadSession__rejects_a_malicious_upload_session_ID_%s__rejects',
    async (session_id) => {
      // arrange

      // act
      const res = await call(mcpUploadSession, makeReq({ method: 'GET', params: { session_id } }));

      // assert
      expect(res.status).toHaveBeenCalledWith(400);
      expect(core).toHaveBeenCalledTimes(1);

      expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    },
  );
  it.each([{ user_id: 8 }, { account_id: 10 }, { user_id: [7] }, { account_id: [9] }])(
    'test_mcpUploadToken__rejects_foreign_upload_sessions_%p__rejects',
    async (override) => {
      // arrange
      core.mockResolvedValueOnce(makeSession(override));

      // act
      const res = await call(mcpUploadToken);

      // assert
      expect(res.status).toHaveBeenCalledWith(403);
      expect(core).toHaveBeenCalledTimes(2);

      expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
      expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
    },
  );
  it.each(['expired', 'revoked', 'failed'])(
    'test_mcpUploadToken__never_issues_a_capability_for_a_%s_upload__rejects',
    async (status) => {
      // arrange
      core.mockResolvedValueOnce(makeSession({ status }));

      // act
      const res = await call(mcpUploadToken);

      // assert
      expect(res.status).toHaveBeenCalledWith(410);
      expect(core).toHaveBeenCalledTimes(2);

      expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
      expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
    },
  );
  it('test_mcpUploadToken__rejects_an_expired_pending_upload__rejects', async () => {
    // arrange
    core.mockResolvedValueOnce(makeSession({ expires_at: '2000-01-01T00:00:00Z' }));

    // act
    const res = await call(mcpUploadToken);

    // assert
    expect(res.status).toHaveBeenCalledWith(410);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
  });
  it('test_mcpUploadSession__keeps_an_owned_attached_session_visible_after_its_up__ok', async () => {
    // arrange
    const session = makeSession({ status: 'attached', expires_at: '2000-01-01T00:00:00Z' });
    core.mockResolvedValueOnce(session);

    // act
    const res = await call(mcpUploadSession, makeReq({ method: 'GET' }));

    // assert
    expect(res.json).toHaveBeenCalledWith({ session, csrf_token: CSRF });
    expect(res.status).not.toHaveBeenCalled();

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
  });
  it('test_mcpUploadToken__does_not_issue_a_new_capability_for_an_attached_s__rejects', async () => {
    // arrange
    core.mockResolvedValueOnce(makeSession({ status: 'attached', expires_at: '2000-01-01T00:00:00Z' }));

    // act
    const res = await call(mcpUploadToken);

    // assert
    expect(res.status).toHaveBeenCalledWith(409);
    expect(core).toHaveBeenCalledTimes(2);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
  });
  it('test_mcpUploadSession__returns_only_storage_verified_session_state_without__ok', async () => {
    // arrange
    core.mockResolvedValueOnce(
      makeSession({ status: 'ready', file_id: 'browser-cannot-use-this', credential: 'secret' }),
    );

    // act
    const res = await call(mcpUploadSession, makeReq({ method: 'GET' }));

    // assert
    expect(res.json).toHaveBeenCalledWith({ session: makeSession({ status: 'ready' }), csrf_token: CSRF });

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
  });
  it('test_mcpUploadToken__issues_a_limited_capability_only_for_the_same_pending__ok', async () => {
    // arrange
    core.mockResolvedValueOnce(makeSession()).mockResolvedValueOnce(makeToken());

    // act
    const res = await call(mcpUploadToken);

    // assert
    expect(core).toHaveBeenCalledWith('POST', `/integrations/mcp/uploads/${ID}/token`, TOKEN, {});
    expect(res.json).toHaveBeenCalledWith({
      access_token: makeToken().access_token,
      upload_session_id: ID,
      file_upload_url: makeToken().file_upload_url,
      expires_in: 300,
    });

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(3);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
    expect(core).toHaveBeenNthCalledWith(3, 'POST', `/integrations/mcp/uploads/${ID}/token`, TOKEN, {});
  });
  it.each([
    { file_upload_url: 'https://evil.example/upload' },
    { access_token: 'mcp-d_wrong' },
    { access_token: [makeToken().access_token] },
    { upload_session_id: 'other' },
  ])('test_mcpUploadToken__rejects_an_unsafe_upload_capability_%p__rejects', async (override) => {
    // arrange
    core.mockResolvedValueOnce(makeSession()).mockResolvedValueOnce(makeToken(override));

    // act
    const res = await call(mcpUploadToken);

    // assert
    expect(res.status).toHaveBeenCalledWith(502);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(3);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
    expect(core).toHaveBeenNthCalledWith(3, 'POST', `/integrations/mcp/uploads/${ID}/token`, TOKEN, {});
  });
  it.each([42, ['2099-01-01T00:00:00Z'], null])('отклоняет нестроковый срок согласия %p', async (expires_at) => {
    // arrange
    core.mockResolvedValueOnce(makeConsent({ expires_at }));

    // act
    const res = await call(mcpConsentContext, makeReq({ method: 'GET', query: { request_id: ID } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(502);
    expect(core).toHaveBeenCalledTimes(2);
  });
  it.each([42, ['2099-01-01T00:00:00Z'], null])('отклоняет нестроковый срок загрузки %p', async (expires_at) => {
    // arrange
    core.mockResolvedValueOnce(makeSession({ expires_at }));

    // act
    const res = await call(mcpUploadToken);

    // assert
    expect(res.status).toHaveBeenCalledWith(502);
    expect(core).toHaveBeenCalledTimes(2);
  });
  it('test_mcpUploadToken__rejects_caller_provided_file_IDs_as_completion_ev__rejects', async () => {
    // arrange

    // act
    const res = await call(mcpUploadToken, makeReq({ body: { file_id: 'arbitrary' } }));

    // assert
    expect(res.status).toHaveBeenCalledWith(400);
    expect(core).toHaveBeenCalledTimes(1);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
  });
  it('test_mcpPage__preserves_the_consent_step_when_redirecting_to_password_login__ok', async () => {
    // arrange
    const req = makeReq({
      method: 'GET',
      get: () => undefined,
      originalUrl: `/mcp/connect?request_id=${ID}&step=consent`,
    });
    const res = makeRes();
    const next = jest.fn();

    // act
    await mcpPage(req, res as unknown as Response, next);

    // assert
    expect(res.redirect).toHaveBeenCalledWith(`/auth/signin/?redirectUrl=${encodeURIComponent(req.originalUrl)}`);
    expect(next).not.toHaveBeenCalled();
    expect(core).not.toHaveBeenCalled();
  });
  it('test_mcpPage__renders_MCP_without_putting_the_bearer_token_into_user_contex__ok', async () => {
    // arrange
    const res = makeRes();
    const next = jest.fn();

    // act
    await mcpPage(makeReq({ method: 'GET' }), res as unknown as Response, next);

    // assert
    expect(res.locals).toEqual({ user: makeUser() });
    expect(next).toHaveBeenCalledTimes(1);
    expect(next).toHaveBeenCalledWith();

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenCalledTimes(1);
  });

  it.each([{ created_at: { credential: 'secret' } }, { revoked_at: { credential: 'secret' } }, { revoked_at: '' }])(
    'test_mcpConnections__invalid_dates_%p__rejects_metadata',
    async (override) => {
      // arrange
      core.mockResolvedValueOnce({ results: [makeConnection(override)] });
      const req = makeReq({ method: 'GET' });

      // act
      const res = await call(mcpConnections, req);

      // assert
      expect(res.status).toHaveBeenCalledWith(502);
      expect(res.json).toHaveBeenCalledWith({
        message: 'MCP request failed',
        code: 'unavailable',
        details: { name: 'request', reason: 'MCP request failed' },
      });
      expect(core).toHaveBeenCalledTimes(2);
      expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
      expect(core).toHaveBeenNthCalledWith(2, 'GET', '/integrations/mcp/connections', TOKEN);
    },
  );

  it('test_mcpPage__stale_cookie__returns_to_password_login', async () => {
    // arrange
    core.mockReset();
    core.mockRejectedValueOnce(new McpCoreError(401));
    const req = makeReq({ method: 'GET' });
    const res = makeRes();
    const next = jest.fn();

    // act
    await mcpPage(req, res as unknown as Response, next);

    // assert
    expect(res.redirect).toHaveBeenCalledTimes(1);
    expect(res.redirect).toHaveBeenCalledWith(`/auth/signin/?redirectUrl=${encodeURIComponent(req.originalUrl)}`);
    expect(res.clearCookie).toHaveBeenCalledTimes(1);
    expect(res.clearCookie).toHaveBeenCalledWith('token', { domain: 'my.pneumatic.app', path: '/' });
    expect(core).toHaveBeenCalledTimes(1);
    expect(core).toHaveBeenCalledWith('GET', '/auth/context', TOKEN);
    expect(next).not.toHaveBeenCalled();

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
  });

  it('test_mcpConnect__uppercase_UUID__accepts_canonical_response', async () => {
    // arrange
    const requestId = ID.toUpperCase();
    core.mockResolvedValueOnce({ code: 'code', request_id: ID, expires_in: 60 });
    const req = makeReq({ body: { request_id: requestId } });

    // act
    const res = await call(mcpConnect, req);

    // assert
    expect(res.status).not.toHaveBeenCalled();
    expect(res.json).toHaveBeenCalledWith({
      redirect_url: `https://my.pneumatic.app/oauth/mcp/login?code=code&request_id=${requestId}`,
    });
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenNthCalledWith(2, 'POST', '/integrations/mcp/login-code', TOKEN, { request_id: requestId });
  });

  it('test_mcpConsentContext__uppercase_UUID__accepts_canonical_ID', async () => {
    // arrange
    const requestId = ID.toUpperCase();
    core.mockResolvedValueOnce(makeConsent());
    const req = makeReq({ method: 'GET', query: { request_id: requestId } });

    // act
    const res = await call(mcpConsentContext, req);

    // assert
    expect(res.status).not.toHaveBeenCalled();
    expect(res.json).toHaveBeenCalledWith({
      request_id: requestId,
      client_name: 'Assistant',
      account_name: 'My account',
      scopes: ['pneumatic:read', 'files:write'],
      login_complete: false,
      csrf_token: CSRF,
    });
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/consent?request_id=${requestId}`, TOKEN);
  });

  it('test_mcpUploadSession__uppercase_UUID__reads_canonical_session', async () => {
    // arrange
    core.mockResolvedValueOnce(makeSession());
    const req = makeReq({ method: 'GET', params: { session_id: ID.toUpperCase() } });

    // act
    const res = await call(mcpUploadSession, req);

    // assert
    expect(res.status).not.toHaveBeenCalled();
    expect(res.json).toHaveBeenCalledWith({ session: makeSession(), csrf_token: CSRF });
    expect(core).toHaveBeenCalledTimes(2);
    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', `/integrations/mcp/uploads/${ID}`, TOKEN);
  });

  it('test_mcpRevoke__uppercase_UUID__revokes_canonical_connection', async () => {
    // arrange
    core.mockResolvedValueOnce({ results: [makeConnection()] }).mockResolvedValueOnce(undefined);
    const req = makeReq({ method: 'DELETE', params: { connection_id: ID.toUpperCase() } });

    // act
    const res = await call(mcpRevoke, req);

    // assert
    expect(res.status).toHaveBeenCalledWith(204);
    expect(res.end).toHaveBeenCalledTimes(1);
    expect(res.end).toHaveBeenCalledWith();
    expect(core).toHaveBeenCalledTimes(3);
    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
    expect(core).toHaveBeenNthCalledWith(2, 'GET', '/integrations/mcp/connections', TOKEN);
    expect(core).toHaveBeenNthCalledWith(3, 'DELETE', `/integrations/mcp/connections/${ID}`, TOKEN);
  });

  it('test_mcpConnect__blocked_account__rejects_before_handoff', async () => {
    // arrange
    core.mockReset();
    core.mockResolvedValueOnce({ id: 7, account: { id: 9, is_blocked: true } });
    const req = makeReq({ body: { request_id: ID } });

    // act
    const res = await call(mcpConnect, req);

    // assert
    expect(res.status).toHaveBeenCalledWith(403);
    expect(res.json).toHaveBeenCalledWith({
      message: 'Permission denied',
      code: 'permission_denied',
      details: { name: 'request', reason: 'Permission denied' },
    });
    expect(core).toHaveBeenCalledTimes(1);
    expect(core).toHaveBeenCalledWith('GET', '/auth/context', TOKEN);

    expect(core).toHaveBeenNthCalledWith(1, 'GET', '/auth/context', TOKEN);
  });
});

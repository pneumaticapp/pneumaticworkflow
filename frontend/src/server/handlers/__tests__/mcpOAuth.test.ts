// <reference types="jest" />
import { Request, Response } from 'express';
import { oAuthHandler } from '../oauthHandler';
import { serverApi } from '../../utils';
import { setAuthCookie } from '../../utils/cookie';
import { logServerError } from '../../utils/expectedErrors';

jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../utils/cookie', () => ({ setAuthCookie: jest.fn() }));
jest.mock('../../utils/expectedErrors', () => ({ logServerError: jest.fn() }));
jest.mock('../../../public/utils/getConfig', () => ({ getConfig: () => ({ env: 'prod' }) }));

describe('MCP OAuth continuation', () => {
  const ID = '550e8400-e29b-41d4-a716-446655440000';
  const target = `/mcp/connect?request_id=${ID}&step=consent`;
  const handler = oAuthHandler('/provider/uri', '/provider/token');
  const makeReq = (query: Record<string, unknown> = {}, cookie: string = '') =>
    ({ query, get: () => cookie }) as unknown as Request;
  const makeRes = () => {
    const res = {
      redirect: jest.fn(),
      send: jest.fn(),
      cookie: jest.fn(),
      clearCookie: jest.fn(),
      setHeader: jest.fn(),
      status: jest.fn(),
    };
    res.status.mockReturnValue(res);
    return res;
  };
  const flowCookie = (overrides: Record<string, unknown> = {}) =>
    `mcp-oauth=${encodeURIComponent(JSON.stringify({ target, state: 'oauth-state', provider: '/provider/uri', ...overrides }))}`;

  beforeEach(() => jest.clearAllMocks());
  it('test_oAuthHandler__binds_the_MCP_continuation_to_the_provider_state_in_an_H__ok', async () => {
    // arrange
    (serverApi.get as jest.Mock).mockResolvedValue(
      JSON.stringify({ auth_uri: 'https://provider.example/authorize?state=oauth-state' }),
    );
    const res = makeRes();

    // act
    await handler(makeReq({ redirectUrl: target }), res as unknown as Response);

    // assert
    expect(res.cookie).toHaveBeenCalledWith(
      'mcp-oauth',
      JSON.stringify({ target, state: 'oauth-state', provider: '/provider/uri' }),
      expect.objectContaining({ httpOnly: true, secure: true }),
    );
  });
  it('test_oAuthHandler__returns_to_the_consent_step_after_successful_SSO_and_con__ok', async () => {
    // arrange
    (serverApi.get as jest.Mock).mockResolvedValue(JSON.stringify({ token: 'login-token' }));
    const res = makeRes();

    // act
    await handler(makeReq({ code: 'provider-code', state: 'oauth-state' }, flowCookie()), res as unknown as Response);

    // assert
    expect(setAuthCookie).toHaveBeenCalledTimes(1);
    expect(setAuthCookie).toHaveBeenCalledWith(
      expect.objectContaining({ query: { code: 'provider-code', state: 'oauth-state' } }),
      res,
      { token: 'login-token' },
    );
    expect(res.redirect).toHaveBeenCalledWith(target);
    expect(res.clearCookie).toHaveBeenCalledWith('mcp-oauth', expect.objectContaining({ httpOnly: true }));
    expect(res.clearCookie).toHaveBeenCalledTimes(1);
    expect(res.clearCookie).toHaveBeenCalledWith('mcp-oauth', {
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
    });
  });
  it.each([{ state: 'wrong-state' }, { provider: '/another/uri' }, { target: 'https://evil.example' }])(
    'test_oAuthHandler__rejects_invalid_continuation_binding_%p__rejects',
    async (override) => {
      // arrange
      const res = makeRes();

      // act
      await handler(makeReq({ code: 'code', state: 'oauth-state' }, flowCookie(override)), res as unknown as Response);

      // assert
      expect(res.status).toHaveBeenCalledWith(400);
      expect(setAuthCookie).not.toHaveBeenCalled();
      expect(serverApi.get).not.toHaveBeenCalled();
    },
  );
  it('test_oAuthHandler__does_not_save_an_arbitrary_external_continuation__rejects', async () => {
    // arrange
    (serverApi.get as jest.Mock).mockResolvedValue(
      JSON.stringify({ auth_uri: 'https://provider.example/authorize?state=oauth-state' }),
    );
    const res = makeRes();

    // act
    await handler(makeReq({ redirectUrl: 'https://evil.example' }), res as unknown as Response);

    // assert
    expect(res.cookie).not.toHaveBeenCalled();
  });
  it('test_oAuthHandler__does_not_log_sensitive_provider_errors_for_MCP_flow__rejects', async () => {
    // arrange
    (serverApi.get as jest.Mock).mockRejectedValue({ token: 'sensitive', code: 'sensitive' });
    const res = makeRes();

    // act
    await handler(makeReq({ code: 'code', state: 'oauth-state' }, flowCookie()), res as unknown as Response);

    // assert
    expect(logServerError).not.toHaveBeenCalled();
  });

  it('test_oAuthHandler__missing_state_binding__rejects_callback', async () => {
    // arrange
    const req = makeReq(
      { code: 'provider-code', state: 'oauth-state' },
      `mcp-continuation=${encodeURIComponent(target)}`,
    );
    const res = makeRes();

    // act
    await handler(req, res as unknown as Response);

    // assert
    expect(res.status).toHaveBeenCalledTimes(1);
    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.send).toHaveBeenCalledTimes(1);
    expect(res.send).toHaveBeenCalledWith('Invalid sign-in request');
    expect(serverApi.get).not.toHaveBeenCalled();
    expect(setAuthCookie).not.toHaveBeenCalled();
    expect(logServerError).not.toHaveBeenCalled();
  });

  it('test_oAuthHandler__provider_denies__returns_to_MCP_login', async () => {
    // arrange
    const req = makeReq({ error: 'access_denied', state: 'oauth-state' }, flowCookie());
    const res = makeRes();

    // act
    await handler(req, res as unknown as Response);

    // assert
    expect(res.redirect).toHaveBeenCalledTimes(1);
    expect(res.redirect).toHaveBeenCalledWith(`/auth/signin/?redirectUrl=${encodeURIComponent(target)}`);
    expect(res.clearCookie).toHaveBeenCalledTimes(1);
    expect(res.clearCookie).toHaveBeenCalledWith('mcp-oauth', {
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
    });
    expect(serverApi.get).not.toHaveBeenCalled();
    expect(setAuthCookie).not.toHaveBeenCalled();
    expect(logServerError).not.toHaveBeenCalled();
  });

  it.each(['', ['code', 'code']])('test_oAuthHandler__invalid_code_%p__rejects_callback', async (code) => {
    // arrange
    const req = makeReq({ code, state: 'oauth-state' }, flowCookie());
    const res = makeRes();

    // act
    await handler(req, res as unknown as Response);

    // assert
    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.send).toHaveBeenCalledWith('Invalid sign-in request');
    expect(serverApi.get).not.toHaveBeenCalled();
    expect(setAuthCookie).not.toHaveBeenCalled();
    expect(logServerError).not.toHaveBeenCalled();
  });

  it.each([null, 12, ''])('test_oAuthHandler__invalid_token_%p__keeps_cookie', async (token) => {
    // arrange
    const req = makeReq({ code: 'code', state: 'oauth-state' }, flowCookie());
    const res = makeRes();
    (serverApi.get as jest.Mock).mockResolvedValueOnce(JSON.stringify({ token }));

    // act
    await handler(req, res as unknown as Response);

    // assert
    expect(res.status).toHaveBeenCalledWith(502);
    expect(res.send).toHaveBeenCalledWith('Sign-in unavailable');
    expect(serverApi.get).toHaveBeenCalledTimes(1);
    expect(serverApi.get).toHaveBeenCalledWith(
      '/provider/token?code=code&client_info=undefined&state=oauth-state&session_state=undefined',
    );
    expect(setAuthCookie).not.toHaveBeenCalled();
    expect(logServerError).not.toHaveBeenCalled();
  });
});

import { Request, Response } from 'express';

import { oAuthHandler } from '../oauthHandler';
import { logServerError } from '../../utils/expectedErrors';
import { serverApi } from '../../utils';
import { setAuthCookie } from '../../utils/cookie';

jest.mock('../../utils/expectedErrors', () => ({
  logServerError: jest.fn(),
}));
jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../utils/cookie', () => ({ setAuthCookie: jest.fn() }));
jest.mock('../../../public/constants/routes', () => ({
  ERoutes: {
    Main: '/',
    Register: '/auth/signup/',
  },
}));

type MockRequest = Partial<Request> & {
  query: Record<string, string>;
};

type MockResponse = Partial<Response> & {
  redirect: jest.Mock;
  send: jest.Mock;
};

const createRes = (): MockResponse => ({
  redirect: jest.fn(),
  send: jest.fn(),
});

describe('oAuthHandler', () => {
  const handler = oAuthHandler('/auth/uri', '/auth/token');

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('when code is present (token exchange)', () => {
    const req: MockRequest = {
      query: { code: 'test-code', client_info: 'info', state: 'state', session_state: 'session' },
    };

    it('exchanges code for token and redirects to main', async () => {
      const tokenResponse = JSON.stringify({ token: 'jwt-token' });
      (serverApi.get as jest.Mock).mockResolvedValue(tokenResponse);
      const res = createRes();

      await handler(req as Request, res as Response);

      expect(serverApi.get).toHaveBeenCalledTimes(1);
      expect(setAuthCookie).toHaveBeenCalledTimes(1);
      expect(res.redirect).toHaveBeenCalledTimes(1);
      expect(res.redirect).toHaveBeenCalledWith('/');
    });

    it('uses logServerError when token exchange fails', async () => {
      const apiError = new Error('Token is expired');
      (serverApi.get as jest.Mock).mockRejectedValue(apiError);
      const res = createRes();

      await handler(req as Request, res as Response);

      expect(logServerError).toHaveBeenCalledTimes(1);
      expect(logServerError).toHaveBeenCalledWith(apiError);
    });

    it('redirects to register when token exchange fails', async () => {
      (serverApi.get as jest.Mock).mockRejectedValue(new Error('Token is expired'));
      const res = createRes();

      await handler(req as Request, res as Response);

      expect(res.redirect).toHaveBeenCalledTimes(1);
      expect(res.redirect).toHaveBeenCalledWith('/auth/signup/');
    });
  });

  describe('when no code (auth URI request)', () => {
    const req: MockRequest = { query: {} };

    it('fetches auth URI and sends redirect URI', async () => {
      const authResponse = JSON.stringify({ auth_uri: 'https://login.microsoft.com/...' });
      (serverApi.get as jest.Mock).mockResolvedValue(authResponse);
      const res = createRes();

      await handler(req as Request, res as Response);

      expect(serverApi.get).toHaveBeenCalledTimes(1);
      expect(serverApi.get).toHaveBeenCalledWith('/auth/uri');
      expect(res.send).toHaveBeenCalledTimes(1);
    });

    it('uses logServerError when auth URI fetch fails', async () => {
      const apiError = new Error('Request was throttled');
      (serverApi.get as jest.Mock).mockRejectedValue(apiError);
      const res = createRes();

      await handler(req as Request, res as Response);

      expect(logServerError).toHaveBeenCalledTimes(1);
      expect(logServerError).toHaveBeenCalledWith(apiError);
    });

    it('redirects to register when auth URI fetch fails', async () => {
      (serverApi.get as jest.Mock).mockRejectedValue(new Error('Server Error'));
      const res = createRes();

      await handler(req as Request, res as Response);

      expect(res.redirect).toHaveBeenCalledTimes(1);
      expect(res.redirect).toHaveBeenCalledWith('/auth/signup/');
    });
  });
});

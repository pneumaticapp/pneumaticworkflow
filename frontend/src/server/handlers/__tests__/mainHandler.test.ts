const mockConfig = { api: { urls: { getPages: 'getPages' } }, formSubdomain: 'form-dev.pneumatic.app' };
jest.mock('../../../public/utils/getConfig', () => ({
  getConfig: jest.fn().mockReturnValue(mockConfig),
  serverConfigToBrowser: jest.fn().mockReturnValue(mockConfig),
}));
import { Request, Response } from 'express';
import { mainHandler } from '../mainHandler';
import { serverConfigToBrowser, getConfig } from '../../../public/utils/getConfig';
import { serverApi } from '../../utils';

jest.mock('../../service/checkInvite');
jest.mock('../../utils/cookie');

describe('handlers', () => {
  describe('mainHandler', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      (getConfig as jest.Mock).mockReturnValue(mockConfig);
      (serverConfigToBrowser as jest.Mock).mockReturnValue(mockConfig);
    });
    it('render main file', async () => {
      const req = {
        get: jest.fn(),
        url: '/',
        path: '/',
        baseUrl: '',
        headers: {
          'user-agent': 'windows phone',
        },
        hostname: 'dev.pneumatic.app',
      };
      const res = {
        sendFile: jest.fn(),
        render: jest.fn(),
        redirect: jest.fn(),
        cookie: jest.fn(),
      };
      const env = process.env.MCS_RUN_ENV || 'local';
      jest.spyOn(serverApi, 'get').mockResolvedValueOnce({});

      await mainHandler(req as unknown as Request, res as unknown as Response);

      expect(res.render).toHaveBeenCalledWith('main', {
        config: JSON.stringify(mockConfig),
        env,
        invitedUser: '{}',
        isBuildAnalytics: false,
        pages: '{}',
        user: '{}',
      });
    });
    it('does not redirect to the “main” page if the invited user does not have the required tokens.', async () => {
      const req = {
        get: jest.fn(),
        url: '/',
        path: '/',
        baseUrl: '',
        headers: {
          'user-agent': 'windows phone',
        },
        hostname: 'dev.pneumatic.app',
      };
      const res = {
        sendFile: jest.fn(),
        render: jest.fn(),
        redirect: jest.fn(),
        cookie: jest.fn(),
      };

      await mainHandler(req as unknown as Request, res as unknown as Response);

      expect(res.redirect).not.toHaveBeenCalled();
    });

    it('test_mainHandler__MCP_login_query__omits_bearer', async () => {
      // arrange
      const res = {
        render: jest.fn(),
        redirect: jest.fn(),
        cookie: jest.fn(),
        locals: {
          user: { token: 'session-secret', id: 7, first_name: '</script><script>bad()</script>' },
        },
      };
      const req = {
        get: jest.fn(),
        url: '/auth/signin/',
        path: '/auth/signin/',
        baseUrl: '',
        query: { redirectUrl: '/mcp/connections' },
        headers: { 'user-agent': 'windows phone' },
        hostname: 'dev.pneumatic.app',
        res,
      };
      const pagesMock = jest.spyOn(serverApi, 'get').mockResolvedValueOnce('{}');

      // act
      await mainHandler(req as unknown as Request, res as unknown as Response);

      // assert
      expect(res.render).toHaveBeenCalledTimes(1);
      expect(res.render).toHaveBeenCalledWith(
        'main',
        expect.objectContaining({
          user: '{"id":7,"firstName":"\\u003c/script>\\u003cscript>bad()\\u003c/script>"}',
        }),
      );
      expect(res.redirect).not.toHaveBeenCalled();
      expect(pagesMock).toHaveBeenCalledTimes(1);
      expect(pagesMock).toHaveBeenCalledWith('getPages');
    });
  });
});

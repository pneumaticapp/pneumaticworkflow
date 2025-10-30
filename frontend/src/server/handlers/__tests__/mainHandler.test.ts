const mockConfig = { api: { urls: {} }, formSubdomain: 'form-dev.pneumatic.app' };
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
        headers: {
          'user-agent': 'windows phone',
        },
        hostname: 'dev.pneumatic.app',
      };
      const res = {
        sendFile: jest.fn(),
        render: jest.fn(),
        redirect: jest.fn(),
      };
      const env = process.env.MCS_RUN_ENV || "local";
      jest.spyOn(serverApi, 'get').mockResolvedValueOnce({});

      await mainHandler(req as unknown as Request, res as unknown as Response);

      expect(res.render).toHaveBeenCalledWith('main', {
        config: JSON.stringify(mockConfig),
        env,
        invitedUser: '{}',
        isBuildAnalytics: false,
        pages: "{}",
        user: '{}',
      });
    });
    it('does not redirect to the “main” page if the invited user does not have the required tokens.', async () => {
      const req = {
        get: jest.fn(),
        url: '/',
        headers: {
          'user-agent': 'windows phone',
        },
        hostname: 'dev.pneumatic.app',
      };
      const res = {
        sendFile: jest.fn(),
        render: jest.fn(),
        redirect: jest.fn(),
      };

      await mainHandler(req as unknown as Request, res as unknown as Response);

      expect(res.redirect).not.toHaveBeenCalled();
    });
  });
});

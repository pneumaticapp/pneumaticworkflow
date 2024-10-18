const mockConfig = { api: { urls: {} }, formSubdomain: 'form-dev.pneumatic.app' };
jest.mock('../../../public/utils/getConfig', () => ({
  getConfig: jest.fn().mockReturnValue(mockConfig),
  serverConfigToBrowser: jest.fn().mockReturnValue(mockConfig),
}));
import { Request, Response } from 'express';
import { mainHandler } from '../mainHandler';
import { ERoutes } from '../../../public/constants/routes';
import { mapAuthProfiles } from '../../service/getProfiles';
import { serverConfigToBrowser, getConfig } from '../../../public/utils/getConfig';
import { setAuthCookie } from '../../utils/cookie';
import { serverApi } from '../../utils';

jest.mock('../../service/getProfiles');
jest.mock('../../utils/cookie');

describe('handlers', () => {
  describe('mainHandler', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      (getConfig as jest.Mock).mockReturnValue(mockConfig);
      (serverConfigToBrowser as jest.Mock).mockReturnValue(mockConfig);
      (mapAuthProfiles as jest.Mock).mockResolvedValue({
        invitedUser: {},
        googleAuthUserInfo: {},
      });
    });
    it('рендерит файл main', async () => {
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
        googleAuthUserInfo: '{}',
        env,
        invitedUser: '{}',
        isBuildAnalytics: false,
        pages: "{}",
        user: '{}',
      });
    });
    it('редиректит на "главную", если у пользователя из google есть нужные токены', async () => {
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
      const token = 'some-token';
      (mapAuthProfiles as jest.Mock).mockResolvedValue({
        invitedUser: {},
        googleAuthUserInfo: { token },
      });

      await mainHandler(req as unknown as Request, res as unknown as Response);

      expect(setAuthCookie).toHaveBeenCalledWith(req, res, { token });
      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Main);
    });
    it('не редиректит на "главную", если у приглашённого пользователя нет нужных токенов', async () => {
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
      const access = '';
      (mapAuthProfiles as jest.Mock).mockResolvedValue({
        invitedUser: { access },
        googleAuthUserInfo: {},
      });

      await mainHandler(req as unknown as Request, res as unknown as Response);

      expect(res.redirect).not.toHaveBeenCalled();
    });
  });
});

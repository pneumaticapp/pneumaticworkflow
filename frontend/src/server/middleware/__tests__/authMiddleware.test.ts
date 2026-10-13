import { authMiddleware } from '../authMiddleware';
import { ERoutes } from '../../../public/constants/routes';
import { parseCookies } from '../../../public/utils/cookie';
import { setAuthCookie, setGuestCookie } from '../../utils/cookie';
import { IAuthenticatedUser } from '../../utils/types';
import { getUser } from '../utils/getUser';

jest.mock('../../../public/utils/cookie');
jest.mock('../../utils/cookie');
jest.mock('../../utils/request', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../utils/getUser');
jest.mock('../../utils/cookie');

const req: any = {
  header: jest.fn(),
  get: jest.fn(),
  url: '/',
  path: '/',
  baseUrl: '',
  headers: {
    'user-agent': 'windows phone',
  },
  hostname: 'dev.pneumatic.app',
};
const res: any = {
  cookie: jest.fn(),
  redirect: jest.fn(),
  locals: {},
};
const next = jest.fn();

describe('middleware', () => {
  describe('authMiddleware', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      res.locals.user = {};
      (parseCookies as jest.Mock).mockReturnValue({});
    });
    it('calls next() if no saved token and requested url is an authorization url', async () => {
      const url = '/auth/signin/';
      await authMiddleware({ ...req, url }, res, next);

      expect(next).toHaveBeenCalled();
    });
    it('redirects to Sign In with redirectUrl parameter if requested inner page with no token', async () => {
      (parseCookies as jest.Mock).mockReturnValueOnce({ token: '' });

      await authMiddleware({ ...req, url: '/dashboard/' }, res, next);

      expect(res.redirect).toHaveBeenCalledWith(`${ERoutes.Login}?redirectUrl=%2Fdashboard%2F`);
    });
    it('redirects already signed account owner to the Dashboard', async () => {
      const mockUser = { is_account_owner: true, account: { is_subscribed: true } } as IAuthenticatedUser;
      (getUser as jest.Mock).mockReturnValue(mockUser);
      (parseCookies as jest.Mock).mockReturnValueOnce({ token: 'save-token' });
      const url = '/auth/signin/';

      await authMiddleware({ ...req, url }, res, next);

      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Main);
    });
    it('redirects already signed non-account-owner to the Tasks page', async () => {
      const mockUser = { is_account_owner: false, account: { is_subscribed: true } } as IAuthenticatedUser;
      (getUser as jest.Mock).mockReturnValueOnce(mockUser);
      (parseCookies as jest.Mock).mockReturnValueOnce({ token: 'save-token' });
      const url = '/auth/signin/';

      await authMiddleware({ ...req, url }, res, next);

      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Tasks);
    });
    it('set guest-token cookie if requested url is a Guest Task', async () => {
      const token = 'guest-token';
      const url = '/guest-task/';
      const guestPageReq = { ...req, url, query: { token } };
      await authMiddleware(guestPageReq, res, next);

      expect(setGuestCookie).toHaveBeenCalledWith(guestPageReq, res, token);
    });
    it('calls next() if requested url is a Guest Task', async () => {
      const token = 'guest-token';
      const url = '/guest-task/';
      const guestPageReq = { ...req, url, query: { token } };
      await authMiddleware(guestPageReq, res, next);

      expect(next).toHaveBeenCalled();
    });

    it('test_authMiddleware__MCP_no_plan__returns_to_consent', async () => {
      // arrange
      const target = '/mcp/connect?request_id=550e8400-e29b-41d4-a716-446655440000&step=consent';
      const user = { id: '7', account: { id: 9, is_subscribed: false, billing_plan: null } };
      const request = {
        ...req,
        url: '/auth/signin/',
        query: { redirectUrl: target },
        get: jest.fn().mockReturnValue('token=cookie-session'),
      };
      const response = { ...res, setHeader: jest.fn() };
      (getUser as jest.Mock).mockResolvedValueOnce(user);

      // act
      await authMiddleware(request, response, next);

      // assert
      expect(response.redirect).toHaveBeenCalledTimes(1);
      expect(response.redirect).toHaveBeenCalledWith(target);
      expect(getUser).toHaveBeenCalledTimes(1);
      expect(getUser).toHaveBeenCalledWith(request, 'cookie-session', 'windows phone');
      expect(next).not.toHaveBeenCalled();
      expect(setAuthCookie).not.toHaveBeenCalled();
    });

    it('test_authMiddleware__MCP_query_token__ignores_credential', async () => {
      // arrange
      const target = '/mcp/connections';
      const request = {
        ...req,
        url: '/auth/signin/',
        query: { redirectUrl: target, mobile_app_token: 'attacker-token' },
        get: jest.fn().mockReturnValue(''),
      };
      const response = { ...res, setHeader: jest.fn() };

      // act
      await authMiddleware(request, response, next);

      // assert
      expect(next).toHaveBeenCalledTimes(1);
      expect(next).toHaveBeenCalledWith();
      expect(response.redirect).not.toHaveBeenCalled();
      expect(getUser).not.toHaveBeenCalled();
      expect(setAuthCookie).not.toHaveBeenCalled();
    });
  });
});

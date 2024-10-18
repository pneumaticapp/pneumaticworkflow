import { authMiddleware } from '../authMiddleware';
import { ERoutes } from '../../../public/constants/routes';
import { parseCookies } from '../../../public/utils/cookie';
import { setGuestCookie } from '../../utils/cookie';
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
    it('calls next() in case requested url is in EXCLUDED_ROUTES', async () => {
      const url = '/static/favicon.ico';

      await authMiddleware({ ...req, url }, res, next);

      expect(next).toHaveBeenCalled();
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
      const mockUser = { is_account_owner: true, account: { payment_card_provided: true } } as IAuthenticatedUser;
      (getUser as jest.Mock).mockReturnValue(mockUser);
      (parseCookies as jest.Mock).mockReturnValueOnce({ token: 'save-token' });
      const url = '/auth/signin/';

      await authMiddleware({ ...req, url }, res, next);

      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Main);
    });
    it('redirects already signed non-account-owner to the Tasks page', async () => {
      const mockUser = { is_account_owner: false, account: { payment_card_provided: true } } as IAuthenticatedUser;
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
  });
});

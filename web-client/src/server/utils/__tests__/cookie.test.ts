import { setAuthCookie } from '../cookie';

describe('cookie', () => {
  it('sets a cookie.', () => {
    const domain = 'dev.pneumatic.com';
    const tokens = {
      token: 'token',
    };
    const req: any = { hostname: domain };
    const res: any = { cookie: jest.fn() };

    setAuthCookie(req, res, tokens);

    expect(res.cookie).toHaveBeenCalledWith('token', tokens.token, { domain });
  });
});

import { oauthGoogleHandler } from '../oauthGoogleHandler';
import { Request, Response } from 'express';
import { ERoutes } from '../../../public/constants/routes';
import { mapGooglePeopleResponse } from '../../mappers';
import { setAuthCookie } from '../../utils/cookie';
import { serverApi } from '../../utils';
import { logger } from '../../../public/utils/logger';
import { getGoogleOauthClient } from '../../service/getGoogleOauthClient';
import { google } from 'googleapis';

jest.mock('googleapis');
jest.mock('../../mappers/mapGooglePeopleResponse');
jest.mock('../../utils/cookie');
jest.mock('../../service/getGoogleOauthClient');

const mockRequest = {
  query: { code: 'google-oauth-code' },
};

const res = {
  redirect: jest.fn(),
  send: jest.fn(),
} as unknown as Response;

const getRequest = (part?: Partial<Request>) =>
  ({
    ...mockRequest,
    ...part,
    headers: {
      'user-agent': 'windows phone',
    },
  } as Request);

const mockGoogleUser = {
  email: 'example@pneumatic.com',
  firstName: 'Example',
  lastName: 'Test',
  companyName: 'Pneumatic',
  phone: '',
  photo: '/google/photo.jpg',
};

const getToken = jest.fn();
const generateAuthUrl = jest.fn();
const peopleGet = jest.fn();
const people = { people: { get: peopleGet } };

describe('handlers', () => {
  describe('oauthGoogleHandler', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      getToken.mockReturnValue({ tokens: {} });
      generateAuthUrl.mockReturnValue('google-redirect-uri');
      (getGoogleOauthClient as jest.Mock).mockReturnValue({ getToken, generateAuthUrl });
      (google.people as jest.Mock).mockReturnValue(people);
    });
    it('если пришёл код получает токен и пытается авторизоваться через него', async () => {
      const req = getRequest();
      const tokens = { access: 'some-token', refresh: 'some-refresh-token' };
      jest.spyOn(serverApi, 'post').mockResolvedValueOnce(tokens);
      (mapGooglePeopleResponse as jest.Mock).mockReturnValueOnce(mockGoogleUser);
      peopleGet.mockResolvedValueOnce({ data: { ok: true } });

      await oauthGoogleHandler(req, res);

      expect(setAuthCookie).toHaveBeenCalledWith(req, res, tokens);
      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Main);
    });
    it('если не удаётся авторизоваться пытается зарегистрироваться с полученными данными', async () => {
      const req = getRequest();
      const loginError = { code: 'user_not_exists' };
      const errorSpy = jest.spyOn(logger, 'error');
      const googleAuthToken = 'some-token-value';
      const postSpy = jest.spyOn(serverApi, 'post');
      postSpy.mockRejectedValueOnce(loginError);
      postSpy.mockResolvedValueOnce({ token: googleAuthToken });
      (mapGooglePeopleResponse as jest.Mock).mockReturnValueOnce(mockGoogleUser);
      peopleGet.mockResolvedValueOnce({ data: { ok: true } });

      await oauthGoogleHandler(req, res);

      expect(errorSpy).toHaveBeenCalledWith(loginError);
      expect(res.redirect).toHaveBeenCalledWith(`${ERoutes.SignUpGoogle}?token=${googleAuthToken}`);
    });
    it('если не удаётся авторизоваться и зарегистрироваться редиректит на регистрацию', async () => {
      const req = getRequest();
      const loginError = { code: 'user_not_exists' };
      const registerError = { code: 'register_exists' };
      const errorSpy = jest.spyOn(logger, 'error');
      jest.spyOn(serverApi, 'post').mockRejectedValueOnce(loginError);
      jest.spyOn(serverApi, 'post').mockRejectedValueOnce(registerError);
      (mapGooglePeopleResponse as jest.Mock).mockReturnValueOnce(mockGoogleUser);
      peopleGet.mockResolvedValueOnce({ data: { ok: true } });

      await oauthGoogleHandler(req, res);

      expect(errorSpy).toHaveBeenCalledTimes(2);
      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Register);
    });
    it('если не пришёл code отдаёт в формате json нужную ссылку для редиректа', async () => {
      const req = getRequest({ query: {} });

      await oauthGoogleHandler(req, res);

      expect(res.send).toHaveBeenCalledWith(JSON.stringify({ redirectUri: 'google-redirect-uri' }));
    });
  });
});

import { Request, Response } from 'express';
import { serverApi } from '../../utils';
import { invitesGoogleHandler } from '../invitesGoogleHandler';
import { mapGoogleUserList } from '../../mappers/mapGoogleUserList';
import { google } from 'googleapis';
import { getGoogleOauthClient } from '../../service/getGoogleOauthClient';
import { logger } from '../../../public/utils/logger';

jest.mock('googleapis');
jest.mock('../../service/getGoogleOauthClient');
jest.mock('../../mappers/mapGoogleUserList');

const getToken = jest.fn();
const generateAuthUrl = jest.fn();

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
  } as Request);

const mockGoogleUser = {
  email: 'example@pneumatic.com',
  firstName: 'Example',
  lastName: 'Test',
  companyName: 'Pneumatic',
  phone: '',
  photo: '/google/photo.jpg',
};

describe('handlers', () => {
  describe('invitesGoogleHandler', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      getToken.mockReturnValue({ tokens: {} });
      generateAuthUrl.mockReturnValue('google-redirect-uri');
      (getGoogleOauthClient as jest.Mock).mockReturnValue({ getToken, generateAuthUrl });
    });
    it('if a code is received, it fetches users using the users.list method and sends them as a “script”', async () => {
      const req = getRequest();
      const googleApiUsers: any = { users: [] };
      const tokens = { access: 'some-token', refresh: 'some-refresh-token' };
      const users = [mockGoogleUser];
      const usersList = jest.fn().mockResolvedValueOnce({ data: googleApiUsers });
      (google.admin as jest.Mock).mockReturnValue({ users: { list: usersList } });
      jest.spyOn(serverApi, 'post').mockResolvedValueOnce(tokens);
      (mapGoogleUserList as jest.Mock).mockReturnValueOnce(users);
      const data = JSON.stringify({ googleUsers: users });
      const expectedBody = `<script>window.opener.postMessage(${data}, '*');window.close();</script>`;

      await invitesGoogleHandler(req, res);

      expect(res.send).toHaveBeenCalledWith(expectedBody);
    });
    it('upon an error in fetching users, it sends the received errors as a “script”', async () => {
      const req = getRequest();
      const tokens = { access: 'some-token', refresh: 'some-refresh-token' };
      const users = [mockGoogleUser];
      const error = { errors: ['Unavailable'] };
      const usersList = jest.fn().mockRejectedValueOnce(error);
      (google.admin as jest.Mock).mockReturnValue({ users: { list: usersList } });
      jest.spyOn(serverApi, 'post').mockResolvedValueOnce(tokens);
      (mapGoogleUserList as jest.Mock).mockReturnValueOnce(users);
      const data = JSON.stringify({ errors: ['Unavailable'] });
      const expectedBody = `<script>window.opener.postMessage(${data}, '*');window.close();</script>`;

      await invitesGoogleHandler(req, res);

      expect(res.send).toHaveBeenCalledWith(expectedBody);
    });
    it('upon an error in fetching users, it sends an empty list of errors.', async () => {
      const req = getRequest();
      const tokens = { access: 'some-token', refresh: 'some-refresh-token' };
      const users = [mockGoogleUser];
      const error = { code: '503' };
      const usersList = jest.fn().mockRejectedValueOnce(error);
      (google.admin as jest.Mock).mockReturnValue({ users: { list: usersList } });
      jest.spyOn(serverApi, 'post').mockResolvedValueOnce(tokens);
      (mapGoogleUserList as jest.Mock).mockReturnValueOnce(users);
      const data = JSON.stringify({ errors: [] });
      const expectedBody = `<script>window.opener.postMessage(${data}, '*');window.close();</script>`;
      const loggerError = jest.spyOn(logger, 'error');

      await invitesGoogleHandler(req, res);

      expect(res.send).toHaveBeenCalledWith(expectedBody);
      expect(loggerError).toHaveBeenCalledWith(error);
    });
    it('if the code is not received, return the URL for invites.', async () => {
      const req = getRequest({ query: {} });

      await invitesGoogleHandler(req, res);

      expect(res.redirect).toHaveBeenCalledWith('google-redirect-uri');
    });
  });
});

import * as request from 'request';
import { Request, Response } from 'express';

import { parseCookies } from '../../../public/utils/cookie';
import { apiProxy } from '../';
import { serverApi } from '../../utils';
import { getAuthHeader } from '../../utils/getAuthHeader';
import { logger } from '../../../public/utils/logger';
import { ERoutes } from '../../../public/constants/routes';

jest.mock('../../../public/utils/cookie');
jest.mock('../../utils/getAuthHeader');
jest.mock('request');

const req = {
  body: { 1: 2 },
  get: jest.fn(),
  headers: {
    'X-Header': 'ok',
  },
  params: {
    path: '/auth/token/obtain',
  },
  url: '/api/auth/token/obtain',
  originalUrl: '/api/auth/token/obtain',
  hostname: 'dev.pneumatic.app',
} as unknown as Request;

const res = {
  status: jest.fn(),
  send: jest.fn().mockImplementation(() => res),
  redirect: jest.fn(),
} as unknown as Response;
const url = 'https://dev.pneumatic.app/auth/token/obtain';

describe('handlers', () => {
  describe('apiProxy', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      (parseCookies as jest.Mock).mockReturnValue({});
      jest.spyOn(serverApi, 'getUrl').mockReturnValue(url);
      jest.spyOn(serverApi, 'getUrl').mockReturnValue(url);
      (res.status as jest.Mock).mockImplementation(() => res);
      (res.send as jest.Mock).mockImplementation(() => res);
    });
    it('calls the passed method with the required parameters', async () => {
      const pipe = jest.fn();
      const on = jest.fn().mockReturnValue({ pipe });
      const postMock = request.post as jest.Mock;
      const headers = {
        ...req.headers,
        Host: 'dev.pneumatic.app',
        'Content-Type': 'application/json',
      };
      postMock.mockReturnValue({ on } as unknown as request.Request);
      const post = apiProxy('post');

      post(req, res);

      expect(postMock).toHaveBeenCalledWith(url, { body: req.body, headers, rejectUnauthorized: false, json: true });
    });
    it('in case of an error, returns a 500 status and logs the error', async () => {
      const pipe = jest.fn();
      const on = jest.fn().mockReturnValue({ pipe });
      const postMock = request.post as jest.Mock;
      const authHeader = { Authorization: 'Bearer SomeToken' };
      (getAuthHeader as jest.Mock).mockReturnValue(authHeader);
      const errorSpy = jest.spyOn(logger, 'error');
      postMock.mockReturnValue({ on } as unknown as request.Request);
      const error = 'Some Bad Error';
      const post = apiProxy('post');
      const msg = 'Error on connecting to API.';

      post(req, res);
      const onError = on.mock.calls[0][1];
      onError(error);

      expect(errorSpy).toHaveBeenCalledWith(msg, error);
      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.send).toHaveBeenCalledWith(msg);
    });
    it('redirects to 404 if the path is not allowed', async () => {
      const post = apiProxy('get');
      const anotherReq = { ...req, originalUrl: '/api/auth' };

      post(anotherReq as unknown as Request, res);

      expect(res.redirect).toHaveBeenCalledWith(ERoutes.Error);
    });
  });
});

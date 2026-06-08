import { Request, Response } from 'express';

import { verificateAccountMiddleware } from '../verificateAccountMiddleware';
import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';

jest.mock('../../../public/utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
}));
jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../../public/constants/routes', () => ({
  ERoutes: {
    AccountVerification: '/auth/verification/:token',
    Login: '/auth/signin/',
  },
}));

type MockRequest = Partial<Request> & {
  query: { token: string };
};

type MockResponse = Partial<Response> & {
  redirect: jest.Mock;
};

describe('verificateAccountMiddleware', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls API with token from query and redirects to login on success', async () => {
    (serverApi.get as jest.Mock).mockResolvedValue({});
    const req: MockRequest = { query: { token: 'valid-token' } };
    const res: MockResponse = { redirect: jest.fn() };

    await verificateAccountMiddleware(req as Request, res as Response);

    expect(serverApi.get).toHaveBeenCalledTimes(1);
    expect(serverApi.get).toHaveBeenCalledWith('/auth/verification/valid-token', {}, true);
    expect(res.redirect).toHaveBeenCalledTimes(1);
    expect(res.redirect).toHaveBeenCalledWith('/auth/signin/');
  });

  it('logs with info level (not error) when API call fails', async () => {
    const apiError = new Error('Token is invalid');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);
    const req: MockRequest = { query: { token: 'invalid-token' } };
    const res: MockResponse = { redirect: jest.fn() };

    await verificateAccountMiddleware(req as Request, res as Response);

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.info).toHaveBeenCalledWith(apiError);
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('redirects to login even when API call fails', async () => {
    (serverApi.get as jest.Mock).mockRejectedValue(new Error('Token is invalid'));
    const req: MockRequest = { query: { token: 'bad-token' } };
    const res: MockResponse = { redirect: jest.fn() };

    await verificateAccountMiddleware(req as Request, res as Response);

    expect(res.redirect).toHaveBeenCalledTimes(1);
    expect(res.redirect).toHaveBeenCalledWith('/auth/signin/');
  });
});

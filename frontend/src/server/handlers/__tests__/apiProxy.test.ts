import { Request, Response } from 'express';
import type { Options } from 'http-proxy-middleware';

import { apiProxy } from '../';
import { serverApi } from '../../utils';
import { logger } from '../../../public/utils/logger';
import { ERoutes } from '../../../public/constants/routes';

jest.mock('../../../public/utils/cookie');
jest.mock('../../utils/getAuthHeader');
jest.mock('http-proxy-middleware', () => ({
  createProxyMiddleware: jest.fn(),
  fixRequestBody: jest.fn(),
}));

interface IMockHttpProxyMiddleware {
  createProxyMiddleware: jest.Mock<jest.Mock, [Options<Request, Response>]>;
  fixRequestBody: jest.Mock;
}

interface IMockCookie {
  parseCookies: jest.Mock<Record<string, string>, [Request]>;
}

const { createProxyMiddleware, fixRequestBody }: IMockHttpProxyMiddleware = require('http-proxy-middleware');
const { parseCookies }: IMockCookie = require('../../../public/utils/cookie');

type TProxyHandler = ReturnType<typeof apiProxy>;
type TProxyRequest = Parameters<TProxyHandler>[0];
type TProxyResponse = Parameters<TProxyHandler>[1];

interface IMockResponseContext {
  res: TProxyResponse;
  statusMock: jest.Mock;
  sendMock: jest.Mock;
  redirectMock: jest.Mock;
}

function createMockRequest(overrides?: Partial<TProxyRequest>): TProxyRequest {
  const defaultReq: Partial<TProxyRequest> = {
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
  };

  return {
    ...defaultReq,
    ...overrides,
  } as TProxyRequest;
}

function createMockResponse(): IMockResponseContext {
  const statusMock = jest.fn().mockReturnThis();
  const sendMock = jest.fn().mockReturnThis();
  const redirectMock = jest.fn();

  const res: Partial<TProxyResponse> = {
    status: statusMock,
    send: sendMock,
    redirect: redirectMock,
  };

  return {
    res: res as TProxyResponse,
    statusMock,
    sendMock,
    redirectMock,
  };
}

const targetUrl = 'https://dev.pneumatic.app/auth/token/obtain';

describe('handlers', () => {
  describe('apiProxy', () => {
    const mockMiddleware = jest.fn();

    beforeEach(() => {
      jest.clearAllMocks();
      createProxyMiddleware.mockReturnValue(mockMiddleware);
      parseCookies.mockReturnValue({});
      jest.spyOn(serverApi, 'getProxyUrl').mockReturnValue(targetUrl);
    });

    it('configures createProxyMiddleware and invokes it on allowed route', () => {
      const handler = apiProxy();
      const req = createMockRequest();
      const { res } = createMockResponse();

      handler(req, res);

      expect(createProxyMiddleware).toHaveBeenCalledTimes(1);

      const proxyConfig = createProxyMiddleware.mock.calls[0][0];

      expect(proxyConfig.changeOrigin).toBe(true);
      expect(proxyConfig.on?.proxyReq).toBe(fixRequestBody);
      expect(typeof proxyConfig.router).toBe('function');
      if (typeof proxyConfig.router === 'function') {
        expect(proxyConfig.router(req)).toBe('https://dev.pneumatic.app');
      }
      expect(typeof proxyConfig.pathRewrite).toBe('function');
      if (typeof proxyConfig.pathRewrite === 'function') {
        expect(proxyConfig.pathRewrite(req.url, req)).toBe('/auth/token/obtain');
      }

      expect(mockMiddleware).toHaveBeenCalledTimes(1);
      expect(mockMiddleware).toHaveBeenCalledWith(req, res, expect.any(Function));
    });

    it('in case of an error, returns a 500 status and logs the error', () => {
      const errorSpy = jest.spyOn(logger, 'error');
      const error = new Error('Some Bad Error');
      const handler = apiProxy();
      const msg = 'Error on connecting to API.';
      const req = createMockRequest();
      const { res, statusMock, sendMock } = createMockResponse();

      handler(req, res);

      const proxyConfig = createProxyMiddleware.mock.calls[0][0];
      const onError = proxyConfig.on?.error;
      if (onError) {
        onError(error, req, res);
      }

      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy).toHaveBeenCalledWith(msg, error);
      expect(statusMock).toHaveBeenCalledTimes(1);
      expect(statusMock).toHaveBeenCalledWith(500);
      expect(sendMock).toHaveBeenCalledTimes(1);
      expect(sendMock).toHaveBeenCalledWith(msg);
    });

    it('redirects to 404 if the path is not allowed', () => {
      const handler = apiProxy();
      const anotherReq = createMockRequest({ originalUrl: '/api/auth' });
      const { res, redirectMock } = createMockResponse();

      handler(anotherReq, res);

      expect(redirectMock).toHaveBeenCalledTimes(1);
      expect(redirectMock).toHaveBeenCalledWith(ERoutes.Error);
      expect(mockMiddleware).not.toHaveBeenCalled();
    });
  });
});

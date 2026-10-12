import { get } from 'request';
import { isRouteAllowed, serverApi } from '../request';

jest.mock('request', () => ({ get: jest.fn() }));

describe('utils', () => {
  describe('request', () => {
    beforeEach(() => {
      jest.resetAllMocks();
    });
    it('returns a successfully completed promise with the body if there is no error and the status code is 200 or 201.', async () => {
      const response: any = { statusCode: 200 };
      const body = { body: 'test' };

      const result = serverApi.get('/some/url', {});
      const cb = (get as jest.Mock).mock.calls[0][2];
      cb(undefined, response, body);

      await expect(result).resolves.toEqual(body);
    });
    it('returns a failed promise with the body if the response code is not 200 or 201.', async () => {
      const response: any = { statusCode: 400 };
      const body = { body: 'test' };

      const result = serverApi.get('/api/some/url', {}, true, true);
      const cb = (get as jest.Mock).mock.calls[0][2];
      cb(undefined, response, body);

      await expect(result).rejects.toEqual(body);
    });
    it('returns a failed promise with the body if an error is returned.', async () => {
      const response: any = { statusCode: 200 };
      const body = { body: 'test' };

      const result = serverApi.get('/some/url', {});
      const cb = (get as jest.Mock).mock.calls[0][2];
      cb({}, response, body);

      await expect(result).rejects.toEqual(body);
    });

    it('returns a failed promise with the error object when body is undefined and network error occurred.', async () => {
      const networkError = new Error('connect ECONNREFUSED 127.0.0.1:8001');

      const result = serverApi.get('/some/url', {});
      const callback = (get as jest.Mock).mock.calls[0][2];
      callback(networkError, undefined, undefined);

      await expect(result).rejects.toEqual(networkError);
    });
    it('returns a failed promise with fallback Error when both body and error are undefined.', async () => {
      const response = { statusCode: 500 };

      const result = serverApi.get('/some/url', {});
      const callback = (get as jest.Mock).mock.calls[0][2];
      callback(undefined, response, undefined);

      await expect(result).rejects.toEqual(new Error('Request failed with status 500'));
    });
  });
  describe('isRouteAllowed', () => {
    it('returns true if a permitted link is provided.', () => {
      expect(isRouteAllowed('/api/auth/token/obtain')).toEqual(true);
    });
  });
});

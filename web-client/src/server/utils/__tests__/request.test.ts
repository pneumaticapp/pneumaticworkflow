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
  });
  describe('isRouteAllowed', () => {
    it('returns true if a permitted link is provided.', () => {
      expect(isRouteAllowed('/api/auth/token/obtain')).toEqual(true);
    });
  });
});

import { get } from 'request';
import { isRouteAllowed, serverApi } from '../request';

jest.mock('request', () => ({ get: jest.fn() }));

describe('utils', () => {
  describe('request', () => {
    beforeEach(() => {
      jest.resetAllMocks();
    });
    it('возвращает успешно завершённый промис с body, если нет ошибки и код 200 или 201', async () => {
      const response: any = { statusCode: 200 };
      const body = { body: 'test' };

      const result = serverApi.get('/some/url', {});
      const cb = (get as jest.Mock).mock.calls[0][2];
      cb(undefined, response, body);

      await expect(result).resolves.toEqual(body);
    });
    it('возвращает неудачно завершённый промис с body, если код ответа не 200 или 201', async () => {
      const response: any = { statusCode: 400 };
      const body = { body: 'test' };

      const result = serverApi.get('/api/some/url', {}, true, true);
      const cb = (get as jest.Mock).mock.calls[0][2];
      cb(undefined, response, body);

      await expect(result).rejects.toEqual(body);
    });
    it('возвращает неудачно завершённый промис с body, если вернулась ошибка', async () => {
      const response: any = { statusCode: 200 };
      const body = { body: 'test' };

      const result = serverApi.get('/some/url', {});
      const cb = (get as jest.Mock).mock.calls[0][2];
      cb({}, response, body);

      await expect(result).rejects.toEqual(body);
    });
  });
  describe('isRouteAllowed', () => {
    it('возвращает true, если передать разрешённую ссылку', () => {
      expect(isRouteAllowed('/api/auth/token/obtain')).toEqual(true);
    });
  });
});

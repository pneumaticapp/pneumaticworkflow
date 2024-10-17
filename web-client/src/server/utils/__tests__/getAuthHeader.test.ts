import { getAuthHeader } from '../getAuthHeader';

describe('getAuthHeader', () => {
  it('возвращает хэдер с авторизацией, если предеть токен', () => {
    const token = 'some-token-value';

    const result = getAuthHeader({ token });

    expect(result).toHaveProperty('Authorization', `Bearer ${token}`);
  });
  it('возвращает пустой объект, если не передать токен', () => {
    const result = getAuthHeader();

    expect(result).toEqual({});
  });
});

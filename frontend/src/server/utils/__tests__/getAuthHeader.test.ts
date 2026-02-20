import { EAppPart } from '../../../public/utils/identifyAppPart/types';
import { getAuthHeader } from '../getAuthHeader';

describe('getAuthHeader', () => {
  it('returns the authorization header if a token is provided.', () => {
    const token = 'some-token-value';

    const result = getAuthHeader({ token });

    expect(result).toHaveProperty('Authorization', `Bearer ${token}`);
  });
  it('returns an empty object if no token is provided.', () => {
    const result = getAuthHeader();

    expect(result).toEqual({});
  });

  it('returns an empty object when token is the string "undefined".', () => {
    const result = getAuthHeader({
      token: 'undefined',
      appPart: EAppPart.PublicFormApp,
    });

    expect(result).toEqual({});
  });
});

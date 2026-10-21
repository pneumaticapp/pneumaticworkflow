import { isValidUri } from '../urls';

describe('isValidUri', () => {
  it.each(['http://example.com', 'https://example.com'])('returns true for allowed protocol: %s', (uri) => {
    expect(isValidUri(uri)).toBe(true);
  });

  it.each(['javascript:alert(1)', 'ftp://example.com', 'data:text/html,x'])(
    'returns false for disallowed protocol: %s',
    (uri) => {
      expect(isValidUri(uri)).toBe(false);
    },
  );

  it.each(['not-a-url', '', 'https://'])('returns false when the string is not a URL: "%s"', (uri) => {
    expect(isValidUri(uri)).toBe(false);
  });
});

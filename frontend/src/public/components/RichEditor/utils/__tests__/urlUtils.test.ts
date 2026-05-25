import urlUtils, { normalizeUrl, isUrl } from '../urlUtils';

describe('urlUtils', () => {
  describe('normalizeUrl', () => {
    it('returns empty string for empty input', () => {
      expect(normalizeUrl('')).toBe('');
      expect(normalizeUrl('   ')).toBe('');
    });

    it('adds https:// when protocol is missing', () => {
      expect(normalizeUrl('example.com')).toBe('https://example.com');
      expect(normalizeUrl('pneumatic.app')).toBe('https://pneumatic.app');
    });

    it('does not add protocol when already present', () => {
      expect(normalizeUrl('https://example.com')).toBe('https://example.com');
      expect(normalizeUrl('http://example.com')).toBe('http://example.com');
      expect(normalizeUrl('ftp://files.example.com')).toBe('ftp://files.example.com');
    });

    it('trims whitespace', () => {
      expect(normalizeUrl('  example.com  ')).toBe('https://example.com');
    });

    it('preserves path and query when adding protocol', () => {
      expect(normalizeUrl('example.com/path?q=1')).toBe('https://example.com/path?q=1');
    });

    it('preserves subdomain', () => {
      expect(normalizeUrl('https://api.example.com')).toBe('https://api.example.com');
      expect(normalizeUrl('api.example.com')).toBe('https://api.example.com');
    });
  });

  describe('isUrl', () => {
    it('returns true for valid URLs', () => {
      expect(isUrl('https://example.com')).toBe(true);
      expect(isUrl('http://localhost')).toBe(true);
      expect(isUrl('example.com')).toBe(true);
    });

    it('returns false for invalid URLs', () => {
      expect(isUrl('')).toBe(false);
      expect(isUrl('not a url')).toBe(false);
      expect(isUrl('://missing-host')).toBe(false);
    });

    it('returns true for localhost with port', () => {
      expect(isUrl('http://localhost:3000')).toBe(true);
    });

    it('returns true for URL with path', () => {
      expect(isUrl('https://example.com/foo/bar')).toBe(true);
    });

    it('returns false for only whitespace', () => {
      expect(isUrl('   ')).toBe(false);
    });
  });

  /**
   * Security: dangerous protocols. PROTOCOL_REGEX requires "://", so "javascript:" and "data:"
   * are not treated as protocol; normalizeUrl prepends https. isUrl then uses new URL(normalized)
   * which rejects or misparses these, so isUrl returns false. Safe for link validation.
   */
  describe('security: dangerous protocols', () => {
    it('isUrl rejects javascript: (invalid after normalizeUrl)', () => {
      expect(isUrl('javascript:alert(1)')).toBe(false);
    });

    it('isUrl rejects data: URI', () => {
      expect(isUrl('data:text/html,<script>alert(1)</script>')).toBe(false);
    });

    it('normalizeUrl prepends https for strings without "://" (javascript/data become invalid)', () => {
      expect(normalizeUrl('javascript:void(0)')).toBe('https://javascript:void(0)');
      expect(normalizeUrl('data:text/plain,hello')).toBe('https://data:text/plain,hello');
    });
  });

  describe('default export', () => {
    it('exposes normalizeUrl and isUrl', () => {
      expect(urlUtils.normalizeUrl).toBe(normalizeUrl);
      expect(urlUtils.isUrl).toBe(isUrl);
    });
  });
});

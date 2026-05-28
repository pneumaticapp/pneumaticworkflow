// <reference types="jest" />
import { isFormPath, FORMS_PATH_PREFIX } from '../constants';

describe('isFormPath', () => {
  describe('path-based detection', () => {
    it('returns true when pathname starts with /forms/', () => {
      expect(isFormPath('localhost', '/forms/abc123', '')).toBe(true);
    });

    it('returns true when pathname equals /forms', () => {
      expect(isFormPath('localhost', FORMS_PATH_PREFIX, '')).toBe(true);
    });

    it('returns true for nested path /forms/embed/abc', () => {
      expect(isFormPath('localhost', '/forms/embed/abc', '')).toBe(true);
    });

    it('returns false for /formsome (boundary check)', () => {
      expect(isFormPath('localhost', '/formsome', '')).toBe(false);
    });

    it('returns false for /form (shorter than /forms)', () => {
      expect(isFormPath('localhost', '/form', '')).toBe(false);
    });
  });

  describe('subdomain detection', () => {
    it('returns true when hostname includes formSubdomain', () => {
      expect(isFormPath('form.example.com', '/', 'form.example.com')).toBe(true);
    });

    it('returns false when formSubdomain is empty string', () => {
      expect(isFormPath('localhost', '/', '')).toBe(false);
    });

    it('returns false when formSubdomain is undefined', () => {
      expect(isFormPath('localhost', '/', undefined)).toBe(false);
    });

    it('returns true for partial hostname match (includes behavior)', () => {
      expect(isFormPath('reform.example.com', '/', 'form.example.com')).toBe(true);
    });
  });

  describe('combined — both match', () => {
    it('returns true when both path and subdomain match', () => {
      expect(isFormPath('form.example.com', '/forms/token', 'form.example.com')).toBe(true);
    });
  });

  describe('fallback — neither match', () => {
    it('returns false for regular path with no subdomain', () => {
      expect(isFormPath('localhost', '/dashboard', '')).toBe(false);
    });

    it('returns false for root path with no subdomain', () => {
      expect(isFormPath('localhost', '/', '')).toBe(false);
    });
  });
});

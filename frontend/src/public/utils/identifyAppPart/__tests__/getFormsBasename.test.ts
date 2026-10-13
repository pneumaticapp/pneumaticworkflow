import { getFormsBasename, FORMS_PATH_PREFIX } from '../constants';

describe('getFormsBasename', () => {
  describe('path-based mode — returns FORMS_PATH_PREFIX', () => {
    it('should return "/forms" for /forms/{token}', () => {
      expect(getFormsBasename('/forms/abc123')).toBe(FORMS_PATH_PREFIX);
    });

    it('should return "/forms" for /forms/{token}/ with trailing slash', () => {
      expect(getFormsBasename('/forms/abc123/')).toBe(FORMS_PATH_PREFIX);
    });

    it('should return "/forms" for exact /forms prefix (no token)', () => {
      expect(getFormsBasename('/forms')).toBe(FORMS_PATH_PREFIX);
    });

    it('should return "/forms" for /forms/ with trailing slash only', () => {
      expect(getFormsBasename('/forms/')).toBe(FORMS_PATH_PREFIX);
    });

    it('should return "/forms" for nested path /forms/embed/{token}', () => {
      expect(getFormsBasename('/forms/embed/abc123')).toBe(FORMS_PATH_PREFIX);
    });

    it('should return "/forms" for deep nested path /forms/a/b/c', () => {
      expect(getFormsBasename('/forms/a/b/c')).toBe(FORMS_PATH_PREFIX);
    });

    it('should return "/forms" for UUID token /forms/550e8400-e29b-41d4-a716-446655440000', () => {
      expect(getFormsBasename('/forms/550e8400-e29b-41d4-a716-446655440000')).toBe(FORMS_PATH_PREFIX);
    });
  });

  describe('subdomain mode — returns undefined', () => {
    it('should return undefined for root path /', () => {
      expect(getFormsBasename('/')).toBeUndefined();
    });

    it('should return undefined for /{token} (subdomain mode)', () => {
      expect(getFormsBasename('/abc123')).toBeUndefined();
    });

    it('should return undefined for /{token}/ with trailing slash', () => {
      expect(getFormsBasename('/abc123/')).toBeUndefined();
    });

    it('should return undefined for /embed/{token} (subdomain embed)', () => {
      expect(getFormsBasename('/embed/abc123')).toBeUndefined();
    });

    it('should return undefined for /error/ path', () => {
      expect(getFormsBasename('/error/')).toBeUndefined();
    });
  });

  describe('boundary cases — paths starting with "form" but not "/forms"', () => {
    it('should return undefined for /formsome (no slash after "form")', () => {
      expect(getFormsBasename('/formsome')).toBeUndefined();
    });

    it('should return undefined for /formation/abc', () => {
      expect(getFormsBasename('/formation/abc')).toBeUndefined();
    });

    it('should return undefined for /form (shorter than /forms)', () => {
      expect(getFormsBasename('/form')).toBeUndefined();
    });

    it('should return undefined for /formset/abc', () => {
      expect(getFormsBasename('/formset/abc')).toBeUndefined();
    });

    it('should return undefined for empty path', () => {
      expect(getFormsBasename('')).toBeUndefined();
    });
  });

  describe('security — prevents path traversal or injection', () => {
    it('should return undefined for /Forms/abc (case-sensitive)', () => {
      expect(getFormsBasename('/Forms/abc')).toBeUndefined();
    });

    it('should return undefined for /FORMS/abc (uppercase)', () => {
      expect(getFormsBasename('/FORMS/abc')).toBeUndefined();
    });

    it('should return "/forms" for /forms/../../etc (still starts with /forms/)', () => {
      // The function only checks prefix, path traversal is handled by Express
      expect(getFormsBasename('/forms/../../etc')).toBe(FORMS_PATH_PREFIX);
    });
  });
});

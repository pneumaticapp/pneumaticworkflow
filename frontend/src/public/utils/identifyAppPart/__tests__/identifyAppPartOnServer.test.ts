// <reference types="jest" />
import { identifyAppPartOnServer } from '../identifyAppPartOnServer';
import { EAppPart } from '../types';
import { FORMS_PATH_PREFIX } from '../constants';

jest.mock('../../getConfig', () => ({
  getConfig: jest.fn(),
}));

import { getConfig } from '../../getConfig';

const makeRequest = (overrides: Record<string, unknown> = {}) => ({
  baseUrl: '',
  path: '/',
  hostname: 'localhost',
  url: '/',
  headers: {},
  ...overrides,
} as any);

describe('identifyAppPartOnServer', () => {
  const mockGetConfig = getConfig as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('forms detection', () => {
    it('returns PublicFormApp when baseUrl is FORMS_PATH_PREFIX', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
      const req = makeRequest({ baseUrl: FORMS_PATH_PREFIX, path: '/abc123' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.PublicFormApp);
    });

    it('returns PublicFormApp when path starts with FORMS_PATH_PREFIX/', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
      const req = makeRequest({ path: `${FORMS_PATH_PREFIX}/abc123` });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.PublicFormApp);
    });

    it('returns PublicFormApp for subdomain forms', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: 'form.example.com' });
      const req = makeRequest({ hostname: 'form.example.com' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.PublicFormApp);
    });

    it('returns PublicFormApp when both path and subdomain match', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: 'form.example.com' });
      const req = makeRequest({
        baseUrl: FORMS_PATH_PREFIX,
        path: '/token',
        hostname: 'form.example.com',
      });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.PublicFormApp);
    });

    it('returns MainApp when formSubdomain is empty string (no false positive)', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
      const req = makeRequest({ hostname: 'localhost', path: '/dashboard' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.MainApp);
    });
  });

  describe('guest task', () => {
    beforeEach(() => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
    });

    it('returns GuestTaskApp when url contains /guest-task/', () => {
      const req = makeRequest({ url: '/guest-task/some-token' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.GuestTaskApp);
    });
  });

  describe('priority order', () => {
    it('forms takes priority over guest-task', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
      const req = makeRequest({
        baseUrl: FORMS_PATH_PREFIX,
        path: '/guest-task/token',
        url: '/guest-task/token',
      });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.PublicFormApp);
    });
  });

  describe('main app fallback', () => {
    beforeEach(() => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
    });

    it('returns MainApp for regular paths', () => {
      const req = makeRequest({ path: '/dashboard' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.MainApp);
    });
  });

  describe('edge cases', () => {
    beforeEach(() => {
      mockGetConfig.mockReturnValue({ formSubdomain: '' });
    });

    it('does NOT match /formsome as forms path (boundary check)', () => {
      const req = makeRequest({ path: '/formsome/token' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.MainApp);
    });

    it('does NOT match /form as forms path', () => {
      const req = makeRequest({ path: '/form/token' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.MainApp);
    });

    it('handles formSubdomain=undefined without crashing', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: undefined });
      const req = makeRequest({ path: '/dashboard' });

      expect(identifyAppPartOnServer(req)).toBe(EAppPart.MainApp);
    });

    it('partial hostname match — exact comparison rejects substrings', () => {
      mockGetConfig.mockReturnValue({ formSubdomain: 'form.example.com' });
      const req = makeRequest({ hostname: 'reform.example.com' });

      // hostname === formSubdomain ensures no false positives
      // "reform.example.com" !== "form.example.com"
      expect(identifyAppPartOnServer(req)).toBe(EAppPart.MainApp);
    });
  });
});

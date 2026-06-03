// <reference types="jest" />
import { identifyAppPartOnClient } from '../identifyAppPartOnClient';
import { EAppPart } from '../types';
import { FORMS_PATH_PREFIX } from '../constants';

jest.mock('../../getConfig', () => ({
  getBrowserConfig: jest.fn(),
}));

jest.mock('../../history', () => ({
  history: { location: { pathname: '/' }, push: jest.fn(), listen: jest.fn() },
}));

import { getBrowserConfig } from '../../getConfig';
import { history } from '../../history';

const setWindowLocation = (overrides: Record<string, string> = {}) => {
  Object.defineProperty(window, 'location', {
    value: {
      pathname: '/',
      hostname: 'localhost',
      ...overrides,
    },
    writable: true,
    configurable: true,
  });
};

describe('identifyAppPartOnClient', () => {
  const mockGetBrowserConfig = getBrowserConfig as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    setWindowLocation();
    (history as any).location.pathname = '/';
  });

  describe('forms detection', () => {
    it('returns PublicFormApp for path-based forms (/forms/*)', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: '' } });
      setWindowLocation({ pathname: `${FORMS_PATH_PREFIX}/abc123` });

      expect(identifyAppPartOnClient()).toBe(EAppPart.PublicFormApp);
    });

    it('returns PublicFormApp when pathname equals /forms', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: '' } });
      setWindowLocation({ pathname: FORMS_PATH_PREFIX });

      expect(identifyAppPartOnClient()).toBe(EAppPart.PublicFormApp);
    });

    it('returns PublicFormApp for subdomain forms', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: 'form.example.com' } });
      setWindowLocation({ hostname: 'form.example.com' });

      expect(identifyAppPartOnClient()).toBe(EAppPart.PublicFormApp);
    });

    it('returns PublicFormApp when both path and subdomain match', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: 'form.example.com' } });
      setWindowLocation({
        pathname: `${FORMS_PATH_PREFIX}/token`,
        hostname: 'form.example.com',
      });

      expect(identifyAppPartOnClient()).toBe(EAppPart.PublicFormApp);
    });
  });

  describe('guest task', () => {
    beforeEach(() => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: '' } });
    });

    it('returns GuestTaskApp when history pathname contains /guest-task/', () => {
      (history as any).location.pathname = '/guest-task/some-token';

      expect(identifyAppPartOnClient()).toBe(EAppPart.GuestTaskApp);
    });
  });

  describe('main app fallback', () => {
    beforeEach(() => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: '' } });
    });

    it('returns MainApp for regular paths', () => {
      setWindowLocation({ pathname: '/dashboard' });
      (history as any).location.pathname = '/dashboard';

      expect(identifyAppPartOnClient()).toBe(EAppPart.MainApp);
    });

    it('returns MainApp when formSubdomain is empty string', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: '' } });
      setWindowLocation({ hostname: 'localhost', pathname: '/dashboard' });
      (history as any).location.pathname = '/dashboard';

      expect(identifyAppPartOnClient()).toBe(EAppPart.MainApp);
    });
  });

  describe('edge cases', () => {
    beforeEach(() => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: '' } });
    });

    it('does NOT match /formsome as forms path (boundary check)', () => {
      setWindowLocation({ pathname: '/formsome/token' });

      expect(identifyAppPartOnClient()).toBe(EAppPart.MainApp);
    });

    it('does NOT match /form as forms path', () => {
      setWindowLocation({ pathname: '/form/token' });

      expect(identifyAppPartOnClient()).toBe(EAppPart.MainApp);
    });

    it('handles formSubdomain=undefined without crashing', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: undefined } });
      setWindowLocation({ pathname: '/dashboard' });
      (history as any).location.pathname = '/dashboard';

      expect(identifyAppPartOnClient()).toBe(EAppPart.MainApp);
    });

    it('partial hostname match — exact comparison rejects substrings', () => {
      mockGetBrowserConfig.mockReturnValue({ config: { formSubdomain: 'form.example.com' } });
      setWindowLocation({ hostname: 'reform.example.com' });

      expect(identifyAppPartOnClient()).toBe(EAppPart.MainApp);
    });
  });
});
